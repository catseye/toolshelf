#!/usr/bin/env python

# Copyright (c)2012-2014 Chris Pressey, Cat's Eye Technologies
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

# toolshelf.py:

# Manages the retrieving, docking and building of sources, and creating
# symlinks to the relevant executables in a link farm.

# Still largely under construction.

"""\
toolshelf {options} <subcommand>

Manage sources and links maintained by the toolshelf environment.
Each <subcommand> has its own syntax.  <subcommand> is one of:

    dock {<external-source-spec>}
        Obtain source trees from a remote source, build executables for
        them as needed, and make links to those executables in a link
        farm which is on your executable search path.  Implies `build`
        unless the --no-build option is given.

    build {<docked-source-spec>}
        Build (or re-build) the executables for the given docked sources.

    update {<docked-source-spec>}
        Pull the latest revision of the given docked sources from each's
        upstream repository (which is always the external source from which
        it was originally docked.)  Implies `build` unless the --no-build
        option is given.

    status {<docked-source-spec>}
        Show the `hg status` or `git status`, as appropriate, in their
        naive format, for the given docked sources.

    relink {<docked-source-spec>}
        Update your link farms to contain links to the executables for the given
        docked sources.  Use `relink all` to rebuild the farms from scratch.

    disable {<docked-source-spec>}
        Temporarily remove the links to executables in the given docked projects
        from your link farm.  A subsequent `enable` will restore them.  Note
        that this implies a `relink all` to make sure any previously-shadowed
        links now show up with these sources disabled.

    enable {<docked-source-spec>}
        Restore links to executables for the given docked projects, previously
        disabled.

    show {<docked-source-spec>}
        Display the links that have been put on your linked farm for the
        given docked sources.  Also show the executables those links point to.
        Will also report any broken links and may, in the future, list any
        executables it shadows or is shadowed by.

    resolve {<docked-source-spec>}
        Emit the names of the directories of the docked sources.

    rectify {<docked-source-spec>}
        Traverses the file trees of the given docked source and modifies the
        permissions of files, removing or adding the executable bit based on
        whether toolshelf thinks the file should really be executable or not.

    ghuser [--login <login>] <username>
        Create (on standard output) a catalog for all of the given Github user's
        repositories.  If the --login option is given, the Github API will be
        logged into using the login username (not necessarily the same as the
        target username).  A password will be prompted for the login username.
        If --login is not given, the Github API will be used anonymously, with
        all the caveats that implies.  Note that this command is experimental.

    bbuser --login <login> <username>
        Like ghuser, but for the Bitbucket API.  The --login option is required
        and the login username must be the same as the target username.  (This
        appears to be a limitation of the Bitbucket API.)  Note that this
        command is experimental.
"""

import errno
import fnmatch
import os
import optparse
import re
import subprocess
import sys


__all__ = ['Toolshelf']


### Constants

UNINTERESTING_EXECUTABLES = (
    '.*?(\.txt|\.TXT|\.doc|\.rtf|\.markdown|\.md|\.html|\.css)',
    '.*?(\.png|\.jpg|\.bmp|\.gif|\.svg|\.swf|\.ttf|\.xpm)',
    '.*?(\.so|\.pbxproj|\.c|\.cpp|\.h|\.java|\.strings)',
    '(make|build|compile|clean|install|uninstall)(-cygwin)?(\.sh|\.csh|\.pl|\.py)?',
    '(mkdep|makedep)(-cygwin)?(\.sh|\.csh|\.pl|\.py)?',
    '(configure|Configure|autogen|make-bindist)(-cygwin)?(\.sh|\.csh|\.pl|\.py)?',
    '(run|runme|buildme|doit|setup|__init__)(-cygwin)?(\.sh|\.csh|\.pl|\.py)?',
    '(test(-driver)?|testme|runtests)(-cygwin)?(\.sh|\.csh|\.pl|\.py)?',
    'bench(\.sh|\.csh)',
    # autoconf and automake and libtool stuff
    'config\.status', 'config\.sub', 'config\.guess', 'config\.rpath',
    'missing', 'mkinstalldirs', 'install-sh',
    'ltmain\.sh', 'depcomp', 'libtool',
    'configure\.in', 'configure\.gnu', 'configure\.lineno',
    # perl seems to like these
    'regen',
    # lua projects do this often enough -- note, not actually executable :/
    'test\.lua',
    # seems to be a debian package thing
    'rules',
    # django...
    'manage.py',
    # "project files" that sometimes have the executable bit set
    '(README|INSTALL|COPYING|LICENSE|AUTHORS|authors|CHANGELOG)',
    'Makefile(\.am)?', '\.gitignore', '\.hgignore', 'Rakefile',
    # if they're just digits, they're probably not all that interesting
    '\d\d?\d?\d?(\.sh|\.pl|\.py)?',
    # these executables are not considered "interesting" because if you happen
    # to dock a source which builds an executable by one of these names and
    # toolshelf puts it on the path, you may just have a *wee* problem when
    # trying to build anything else after that point :)
    # you can always declare them to be interesting in a cookie if you want
    'make', 'ant', 'mkdir', 'mv', 'rm',
    'git', 'hg', 'wget', 'unzip', 'tar',
    'cat', 'which', 'install', 'time',
    # whoa, erlang, whoa whoa
    'dirname', 'basename', 'mt',
)

UNINTERESTING_PATHS = (
    'test', 'tests', 'dep', 'deps'
)

HINT_NAMES = (
    'build_command',
    'test_command',
    'exclude_paths',  # TODO: need an include_paths, or interesting_paths, now, too
    'only_paths',
    #'prerequisites',
    'rectify_permissions',
    'require_executables',
    'interesting_executables',
    'python_modules',
    'lua_modules',
    'include_dirs',  # defaults to '/install/include' if it exists
)

LINK_FARM_NAMES = ('bin', 'lib', 'include', 'pkgconfig', 'python', 'lua')

### Exceptions

class CommandLineSyntaxError(ValueError):
    pass


class SourceSpecError(ValueError):
    def __str__(self):
        return repr(self)


class DependencyError(ValueError):
    pass


### Helper Functions


def is_executable(filename):
    return os.path.isfile(filename) and os.access(filename, os.X_OK)


def is_shared_object(filename):
    match = re.match('^.*?\.so$', filename)
    return ((os.path.isfile(filename) or os.path.islink(filename)) and match)


def is_static_lib(filename):
    match = re.match('^.*?\.a$', filename)
    return ((os.path.isfile(filename) or os.path.islink(filename)) and match)


def is_library(filename):
    return is_shared_object(filename) or is_static_lib(filename)


def is_pkgconfig_data(filename):
    if re.match('^.*?\.pc$', filename) is None:
        return False
    if re.match('^.*?\uninstalled\.pc$', filename) is not None:
        return False
    return True


def is_python_package(filename):
    if not os.path.isdir(filename):
        return False
    if os.path.isfile(os.path.join(filename, '__init__.py')):
        return True
    return False


def is_lua_module(filename):
    return filename.endswith('.lua') and os.path.isfile(filename)


def makedirs(dirname):
    try:
        os.makedirs(dirname)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(dirname):
            pass
        else:
            raise

### Classes

# hints are stored under a 'spec key' which is a glob which
# matches a *docked* source spec.

class Cookies(object):
    def __init__(self, shelf):
        self.shelf = shelf
        self._hint_maps = None
        self.filenames = []

    def add_file(self, filename):
        """Will not work after hints have been loaded.
        """
        if os.path.exists(filename):
            self.filenames.append(filename)

    def _load_hints(self):
        self._hint_maps = []
        for filename in self.filenames:
            self._load_hints_from_file(filename)

    def _load_hints_from_file(self, filename):
        hint_map = {}
        with open(filename, 'r') as hints_file:
            spec_key = None
            for line in hints_file:
                line = line.strip()
                if line == '' or line.startswith('#'):
                    continue
                found_hint = False
                for hint_name in HINT_NAMES:
                    pattern = r'^%s(@\w+)?\s+(.*?)\s*$' % hint_name
                    match = re.match(pattern, line)
                    if match:
                        if spec_key is None:
                            raise SourceSpecError(
                                'Found hint %s before any spec' % hint_name
                            )
                        arch_hint_name = hint_name + (match.group(1) or '')
                        hint_value = match.group(2)
                        self.shelf.debug("Adding hint '%s %s' to %s" %
                            (arch_hint_name, hint_value, spec_key)
                        )
                        hint_map[spec_key][arch_hint_name] = hint_value
                        if (hint_name == 'rectify_permissions' and
                            hint_value not in ('yes', 'no')):
                            raise ValueError(
                                "rectify_permissions must be 'yes' or 'no'"
                            )
                        found_hint = True
                        break
                if not found_hint:  # ... then we found a spec
                    spec_key = line
                    hint_map.setdefault(spec_key, {})
        self._hint_maps.append(hint_map)

    @property
    def hint_maps(self):
        if self._hint_maps is None:
            self._load_hints()
        return self._hint_maps

    def apply_hints(self, source):
        for hint_map in self.hint_maps:
            found_in_map = False
            for (key, hints) in hint_map.iteritems():
                pattern = fnmatch.translate(key)
                match = re.match(pattern, source.name)
                if match:
                    source.hints.update(hints)
                    found_in_map = True
            if found_in_map:
                break


class Blacklist(object):
    """A list of sources whose files will not be made available
    in the link farms.
    
    Used by `toolshelf disable/enable`, and persisted.

    """
    def __init__(self, shelf, filename):
        self.shelf = shelf
        self.filename = filename
        self._blacklist_map = set()

    def load(self):
        if not os.path.exists(self.filename):
            return
        with open(self.filename, 'r') as blacklist_file:
            for line in blacklist_file:
                line = line.strip()
                match = re.match(r'^(.*?\/.*?\/.*?)$', line)
                if match:
                    self._blacklist_map.add(match.group(1))
        self.shelf.debug("Loaded blacklist %r" % self._blacklist_map)

    def save(self):
        with open(self.filename, 'w') as blacklist_file:
            for key in self._blacklist_map:
                self.shelf.debug("Saving blacklisted %r" % key)
                blacklist_file.write('%s\n' % key)

    def add(self, source):
        self._blacklist_map.add(source.name)

    def remove(self, source):
        self._blacklist_map.remove(source.name)

    def __contains__(self, source):
        return source.name in self._blacklist_map


class Path(object):
    """For historical purposes only, although may still be used to
    see if executables shadow other executables in the search path.

    """
    def __init__(self, value=None):
        if value is None:
            value = os.environ['PATH']
        self.components = [d.strip() for d in value.split(':')]

    def write(self, result):
        value = ':'.join(self.components)
        result.write("export PATH='%s'\n" % value)

    def remove_components_by_prefix(self, prefix):
        self.components = [d for d in self.components
                           if not d.startswith(prefix)]

    def add_component(self, directory):
        self.components.insert(0, directory)

    def which(self, filename):
        found = []
        for component in self.components:
            full_filename = os.path.join(component, filename)
            if is_executable(full_filename):
                found.append(full_filename)
        return found


class LinkFarm(object):
    """A link farm is a directory which contains symbolic links
    to files (typically executables, libraries, modules, etc.)
    in various other parts of the filesystem.

    """
    def __init__(self, shelf, dirname):
        self.shelf = shelf
        self.dirname = dirname
        makedirs(dirname)

    def links(self):
        for name in os.listdir(self.dirname):
            fullfilename = os.path.join(self.dirname, name)
            if not os.path.islink(fullfilename):
                continue
            source = os.readlink(fullfilename)
            yield (fullfilename, source)

    def get_link(self, filename):
        filename = os.path.realpath(os.path.abspath(filename))
        linkname = os.path.join(self.dirname, os.path.basename(filename))
        if not os.path.islink(linkname):
            return None
        source = os.readlink(linkname)
        return (linkname, source)

    def create_link(self, filename):
        filename = os.path.abspath(filename)
        linkname = os.path.join(self.dirname, os.path.basename(filename))
        # We do trample existing links
        if os.path.islink(linkname):
            # TODO only produce this message if the source link and
            # dest link are in different sources?
            self.shelf.warn("Trampling existing [%s] link %s" %
                (os.path.basename(self.dirname), linkname)
            )
            self.shelf.warn("  was: %s" % os.readlink(linkname))
            self.shelf.warn("  now: %s" % filename)
            os.unlink(linkname)
        self.shelf.symlink(filename, linkname)

    def clean(self, prefix=''):
        for (linkname, sourcename) in self.links():
            if sourcename.startswith(prefix):
                os.unlink(linkname)


class Source(object):
    def __init__(self, shelf, url=None, host=None, user=None, project=None,
                 type=None, local=False, tag=None):
        self.shelf = shelf
        self.url = url
        if not host:
            raise ValueError('no host supplied')
        self.host = host
        self.user = user or 'distfile'
        self.project = project
        self.type = type
        self.local = local
        self.tag = tag
        self.hints = {}
        self.shelf.cookies.apply_hints(self)

    def __repr__(self):
        return ("Source(url=%r, host=%r, user=%r, "
                "project=%r, type=%r, local=%r, tag=%r, hints=%r)" %
                (self.url, self.host, self.user,
                 self.project, self.type, self.local, self.tag, self.hints))

    @property
    def distfile(self):
        if self.local:
            return self.url
        if self.type in ('zip', 'tgz', 'tar.gz', 'tar.xz', 'tar.bz2'):
            return os.path.join(self.shelf.dir, '.distfiles',
                                '%s.%s' % (self.project, self.type))
        else:
            return None

    @property
    def name(self):
        return os.path.join(self.host, self.user, self.project)

    @property
    def user_dir(self):
        return os.path.join(self.shelf.dir, self.host, self.user)

    @property
    def dir(self):
        return os.path.join(self.user_dir, self.project)

    @property
    def docked(self):
        return os.path.isdir(self.dir)

    def checkout(self):
        self.shelf.note("Checking out %s..." % self.name)

        makedirs(self.user_dir)
        self.shelf.chdir(self.user_dir)

        if self.type == 'git':
            self.shelf.run('git', 'clone', self.url)
        elif self.type == 'hg':
            self.shelf.run('hg', 'clone', self.url)
        elif self.type == 'hg-or-git':
            try:
                # better would be to check hg's error output for
                # 'Http Error 406'
                self.shelf.run('hg', 'clone', self.url)
            except subprocess.CalledProcessError:
                self.shelf.note("`hg clone` failed, so trying git")
                self.shelf.run('git', 'clone', self.url)
        elif self.distfile is not None:
            self.shelf.run('mkdir', '-p',
                           os.path.join(self.shelf.dir, '.distfiles'))
            if not os.path.exists(self.distfile):
                if self.local:
                    raise IOError("local distfile '%s' doesn't exist?!" % self.distfile)
                else:
                    self.shelf.run('wget', '-nc', '-O', self.distfile, self.url)
            extract_dir = os.path.join(
                self.shelf.dir, '.extract_' + self.project
            )
            self.shelf.run('mkdir', '-p', extract_dir)
            self.shelf.chdir(extract_dir)
            if self.type == 'zip':
                self.shelf.run('unzip', self.distfile)
            elif self.type in ('tgz', 'tar.gz'):
                self.shelf.run('tar', '-z', '-x', '-v', '-f', self.distfile)
            elif self.type == 'tar.xz':
                self.shelf.run('tar', '-J', '-x', '-v', '-f', self.distfile)
            elif self.type == 'tar.bz2':
                self.shelf.run('tar', '-j', '-x', '-v', '-f', self.distfile)

            files = os.listdir(extract_dir)
            if len(files) == 1:
                self.shelf.note("Archive is well-structured "
                                "(all files in one directory)")
                extracted_dir = os.path.join(extract_dir, files[0])
                if not os.path.isdir(extracted_dir):
                    extracted_dir = extract_dir
            else:
                self.shelf.note("Archive is a 'tarbomb' "
                                "(all files in the root of the archive)")
                extracted_dir = extract_dir
            self.shelf.run('mv', extracted_dir, self.dir)
            self.shelf.run('rm', '-rf', extract_dir)
        else:
            raise NotImplementedError(self.type)
        self.update_to_tag(self.tag)

    def update_to_tag(self, tag):
        """'tag' may also be the name of a branch."""
        if tag is None:
            return
        self.shelf.note("Updating %s to %s..." % (self.dir, tag))
        self.shelf.chdir(self.dir)
        if os.path.isdir('.hg'):
            self.shelf.run('hg', 'up', tag)
        elif os.path.isdir('.git'):
            self.shelf.run('git', 'checkout', tag)
        else:
            self.shelf.warn("Can't update to %s -- not version-controlled" % tag)

    def build(self):
        if not self.shelf.options.build:
            self.shelf.note("SKIPPING build of %s" % self.name)
            return
        self.shelf.note("Building %s..." % self.dir)

        self.shelf.chdir(self.dir)
        build_command = self.hints.get('build_command@' + self.shelf.uname, None)
        if not build_command:
            build_command = self.hints.get('build_command', None)
        if build_command:
            self.shelf.run(build_command, shell=True)
        elif os.path.isfile('build.sh'):
            self.shelf.run('./build.sh')
        elif os.path.isfile('make.sh'):
            self.shelf.run('./make.sh')
        elif os.path.isfile('build.xml'):
            self.shelf.run('ant')
        else:
            if (os.path.isfile('autogen.sh') and
                not os.path.isfile('configure')):
                self.shelf.run('./autogen.sh')
            if (os.path.isfile('configure.in') and
                not os.path.isfile('configure')):
                self.shelf.run('autoconf')
            if os.path.isfile('configure'):
                self.shelf.run('./configure', "--prefix=%s" %
                               os.path.join(self.dir, 'install'))
                self.shelf.run('make')
                self.shelf.run('make', 'install')
            elif os.path.isfile('Makefile') or os.path.isfile('makefile'):
                self.shelf.run('make')
            elif os.path.isfile('src/Makefile'):
                self.shelf.chdir('src')
                self.shelf.run('make')

    def update(self):
        """Returns True if there were changes, False if there were none.

        """
        self.shelf.chdir(self.dir)
        old_head_ref = self.head_ref()
        if os.path.isdir('.git'):
            self.shelf.run('git', 'pull')
        elif os.path.isdir('.hg'):
            self.shelf.run('hg', 'pull', '-u')
        else:
            raise NotImplementedError(
                "Can't update a non-version-controlled Source"
            )
        new_head_ref = self.head_ref()
        return old_head_ref != new_head_ref

    def relink(self):
        """Search this source for linkable files, and place them in
        the link farms.

        Requires that the current directory is self.dir.

        """
        # TODO: refactor all this to make it more efficient.
        self.shelf.link_farms['bin'].clean(prefix=self.dir)
        if self not in self.shelf.blacklist:
            for filename in self.linkable_files(
                              self.is_interesting_executable
                            ):
                self.shelf.link_farms['bin'].create_link(filename)

        self.shelf.link_farms['lib'].clean(prefix=self.dir)
        if self not in self.shelf.blacklist:
            for filename in self.linkable_files(is_library):
                self.shelf.link_farms['lib'].create_link(filename)

        self.shelf.link_farms['python'].clean(prefix=self.dir)
        if self not in self.shelf.blacklist:
            python_modules = self.hints.get('python_modules')
            if python_modules is not None:
                for filename in python_modules.split(' '):
                    self.shelf.link_farms['python'].create_link(filename)
            else:
                for filename in self.linkable_python_packages():
                    self.shelf.link_farms['python'].create_link(filename)                

        self.shelf.link_farms['lua'].clean(prefix=self.dir)
        if self not in self.shelf.blacklist:
            lua_modules = self.hints.get('lua_modules')
            if lua_modules is not None:
                for filename in lua_modules.split(' '):
                    self.shelf.link_farms['lua'].create_link(filename)
            else:
                for filename in self.linkable_files(is_lua_module):
                    if not self.is_interesting(filename):
                        continue
                    self.shelf.link_farms['lua'].create_link(filename)

        self.shelf.link_farms['pkgconfig'].clean(prefix=self.dir)
        if self not in self.shelf.blacklist:
            for filename in self.linkable_files(is_pkgconfig_data):
                self.shelf.link_farms['pkgconfig'].create_link(filename)

        self.shelf.link_farms['include'].clean(prefix=self.dir)
        if self not in self.shelf.blacklist:
            include_dirs = self.hints.get('include_dirs', None)
            if include_dirs is None:
                if os.path.exists(os.path.join(self.dir, 'install', 'include')):
                    include_dirs = 'install/include'
            if include_dirs is not None:
                for dirname in include_dirs.split(' '):
                    if not os.path.isdir(dirname):
                        self.shelf.warn('No such directory: %s' % dirname)
                        continue
                    for filename in os.listdir(dirname):
                        i_filename = os.path.join(dirname, filename)
                        self.shelf.link_farms['include'].create_link(i_filename)

    def status(self):
        self.shelf.chdir(self.dir)
        output = None
        if os.path.isdir('.git'):
            output = self.shelf.get_it('git status')
            if 'working directory clean' in output:
                output = ''
        elif os.path.isdir('.hg'):
            output = self.shelf.get_it('hg status')
        if output:
            print self.dir
            print output

    ### utility methods ###

    def is_interesting(self, filename):
        basename = os.path.basename(filename)
        interesting_executables = self.hints.get('interesting_executables', '').split(' ')
        if basename in interesting_executables:
            return True
        for pattern in UNINTERESTING_EXECUTABLES:
            if re.match('^' + pattern + '$', basename):
                return False
        return True

    def is_interesting_executable(self, filename):
        return self.is_interesting(filename) and is_executable(filename)

    def head_ref(self):
        self.shelf.chdir(self.dir)
        if os.path.isdir('.git'):
            return self.shelf.get_it('git rev-parse HEAD')
        elif os.path.isdir('.hg'):
            return self.shelf.get_it('hg id')
        else:
            raise NotImplementedError(
                "Can't get head ref of a non-version-controlled Source"
            )

    def may_use_path(self, dirname):
        exclude_paths = [p for p in UNINTERESTING_PATHS]        
        exclude_paths_hint = self.hints.get('exclude_paths', None)
        if exclude_paths_hint:
            exclude_paths.extend(exclude_paths_hint.split(' '))
        for path in exclude_paths:
            verboten = os.path.join(self.dir, path)
            if dirname.startswith(verboten):
                return False
        return True

    def linkable_files(self, predicate):
        only_paths = self.hints.get('only_paths', None)
        paths_to_try = [self.dir]
        if only_paths:
            paths_to_try = [
                os.path.join(os.path.join(self.dir, path))
                for path in only_paths.split(' ')
            ]
        for path in paths_to_try:
            for filename in self.find_linkable_file_set(predicate, path):
                yield filename

    def find_linkable_file_set(self, predicate, subdir):
        found_files = {}
        for root, dirs, files in os.walk(os.path.join(self.dir, subdir)):
            if '.git' in dirs:
                dirs.remove('.git')
            if '.hg' in dirs:
                dirs.remove('.hg')
            if not self.may_use_path(root):
                self.shelf.debug("%s excluded from search path" % root)
                dirs[:] = []
                continue
            for name in files:
                filename = os.path.join(self.dir, root, name)
                if predicate(filename):
                    self.shelf.debug("found linkable file: %s" % filename)
                    found_files[os.path.basename(filename)] = filename
        return found_files.values()

    def linkable_python_packages(self):
        for filename in self.find_linkable_dir_set(is_python_package,
                                                   self.dir):
            yield filename

    def find_linkable_dir_set(self, predicate, subdir):
        found_dirs = {}
        for root, dirs, files in os.walk(os.path.join(self.dir, subdir)):
            if '.git' in dirs:
                dirs.remove('.git')
            if '.hg' in dirs:
                dirs.remove('.hg')
            if not self.may_use_path(root):
                self.shelf.debug("%s excluded from search path" % root)
                dirs[:] = []
            remove_these = []
            for name in dirs:
                dirname = os.path.join(self.dir, root, name)
                if predicate(dirname):
                    self.shelf.debug("found linkable dir: %s" % dirname)
                    found_dirs[os.path.basename(dirname)] = dirname
                    remove_these.append(name)
            # now, don't recurse
            for name in remove_these:
                dirs.remove(name)
        return found_dirs.values()

    def rectify_executable_permissions(self):
        for root, dirs, files in os.walk(self.dir):
            if '.git' in dirs:
                dirs.remove('.git')
            if '.hg' in dirs:
                dirs.remove('.hg')
            for name in files:
                filename = os.path.join(self.dir, root, name)
                # if it's not 'interesting', just skip it, so we don't
                # have to call 'file' so many times.  it won't be put on
                # the path anyway, whether it's executable or not.
                if not self.is_interesting(filename):
                    continue
                make_it_executable = False
                pipe = subprocess.Popen(["file", filename],
                                        stdout=subprocess.PIPE)
                output = pipe.communicate()[0]
                self.shelf.debug(output)
                if 'executable' in output:
                    make_it_executable = True
                if make_it_executable:
                    self.shelf.debug("Making %s executable" % filename)
                    subprocess.check_call(["chmod", "u+x", filename])
                else:
                    self.shelf.debug("Making %s NON-executable" % filename)
                    subprocess.check_call(["chmod", "u-x", filename])

    def rectify_permissions_if_needed(self):
        rectify_permissions = 'no'
        if self.type == 'zip':
            rectify_permissions = 'yes'
        rectify_permissions = self.hints.get(
            'rectify_permissions', rectify_permissions
        )
        if rectify_permissions not in ('yes', 'no'):
            raise ValueError(
                "rectify_permissions should be 'yes' or 'no'"
            )
        if rectify_permissions == 'yes':
            self.rectify_executable_permissions()

    def get_latest_release_tag(self, tags={}):
        """Return the tag most recently applied to this repository.
        (hg only for now.)

        """
        self.shelf.chdir(self.dir)

        latest_tag = None
        for line in self.shelf.get_it("hg tags").split('\n'):
            match = re.match(r'^\s*(\S+)\s+(\d+):(.*?)\s*$', line)
            if match:
                tag = match.group(1)
                tags[tag] = int(match.group(2))
                if tag != 'tip' and latest_tag is None:
                    latest_tag = tag

        return latest_tag

    def find_likely_documents(self):
        DOC_PATTERNS = (
            r'^LICENSE$',
            r'^UNLICENSE$',
            r'^README',
            r'^.*?\.markdown$',
            r'^.*?\.md$',
            r'^.*?\.txt$',
            r'^.*?\.lhs$',
        )
        for root, dirnames, filenames in os.walk('.'):
            if root.endswith(".hg"):
                del dirnames[:]
                continue
            for filename in filenames:
                for pattern in DOC_PATTERNS:
                    if re.match(pattern, filename):
                        yield os.path.join(root, filename)[2:]
                        break


### Toolshelf object (Environment and intrinsic subcommands)


class Toolshelf(object):
    def __init__(self, directory=None, uname=None, cwd=None, options=None,
                       cookies=None, blacklist=None, link_farms=None,
                       errors=None):
        if directory is None:
            directory = os.environ.get('TOOLSHELF')
        self.dir = directory

        if cwd is None:
            cwd = os.getcwd()
        self.cwd = cwd

        if options is None:
            class DefaultOptions(object):
                break_on_error = True
                verbose = False
                build = True
            options = DefaultOptions()
        self.options = options

        if uname is None:
            uname = self.get_it('uname').strip()
        self.uname = uname

        if link_farms is None:
            link_farms = {}
        for farm in LINK_FARM_NAMES:
            link_farms.setdefault(farm,
                LinkFarm(self, os.path.join(self.dir, '.' + farm))
            )
        self.link_farms = link_farms

        if cookies is None:
            cookies = Cookies(self)
            cookies.add_file(os.path.join(
                self.dir, '.toolshelf', 'local-cookies.catalog'
            ))
            cookies.add_file(os.path.join(
                self.dir, '.toolshelf', 'cookies.catalog'
            ))
        self.cookies = cookies

        if blacklist is None:
            blacklist = Blacklist(self, os.path.join(
                self.dir, '.toolshelf', 'blacklist.txt'
            ))
            blacklist.load()
        self.blacklist = blacklist

        if errors is None:
            errors = {}
        self.errors = errors

    ### utility methods ###

    def run(self, *args, **kwargs):
        self.note("Running `%s`..." % ' '.join(args))
        if 'ignore_exit_code' in kwargs:
            del kwargs['ignore_exit_code']
            subprocess.call(args, **kwargs)
        else:
            subprocess.check_call(args, **kwargs)

    def get_it(self, command):
        self.note("Running `%s`..." % command)
        output = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE
        ).communicate()[0]
        if self.options.verbose:
            print output
        return output

    def debug(self, msg):
        """Display a debugging message."""
        if self.options.debug:
            print "DEBUG: ", msg

    def note(self, msg):
        """Display an informative message, but only if verbose was selected."""
        if self.options.verbose:
            print "*", msg

    def warn(self, msg):
        """Display a warning, but only if quiet was not selected."""
        if not self.options.quiet:
            print msg

    def chdir(self, dirname):
        self.note("Changing dir to `%s`..." % dirname)
        os.chdir(dirname)

    def symlink(self, sourcename, linkname):
        self.note("Symlinking `%s` to `%s`..." % (linkname, sourcename))
        os.symlink(sourcename, linkname)

    ### persist state ###

    def save(self):
        self.blacklist.save()

    ### making Sources from specs ###

    def expand_docked_spec(self, name):
        """Convert a single docked source specifier into one or more
        expanded source specifiers.

        A docked source specifier may take any of the following forms:

        1. host/user/project          this particular host, user, project
        2. host/user/all              all docked projects by this user & host
        3. user/project               from any host under this name
        4. user/all                   all docked projects by this user
        5. project                    from any host & user under this name
        6. proj+                      first project found that starts w/'proj'
        7. all                        all docked projects
        8. .                          the docked project (if any) in the cwd

        """
        new_specs = []
        match = re.match(r'^([^/]*)/([^/]*)$', name)
        if name == 'all':  # case 7
            for host in sorted(os.listdir(self.dir)):
                if host.startswith('.'):
                    continue
                host_dirname = os.path.join(self.dir, host)
                for user in sorted(os.listdir(host_dirname)):
                    user_dirname = os.path.join(host_dirname, user)
                    for project in sorted(os.listdir(user_dirname)):
                        project_dirname = os.path.join(user_dirname,
                                                       project)
                        if not os.path.isdir(project_dirname):
                            continue
                        new_specs.append('%s/%s/%s' % (host, user, project))
            return new_specs
        elif name == '.':  # case 8
            path = self.cwd
            tsdir = os.path.join(
                path, '..', '..', '..', '.toolshelf'
            )
            if os.path.isdir(tsdir):
                path, project = os.path.split(path)
                path, user = os.path.split(path)
                path, host = os.path.split(path)
                new_specs.append('%s/%s/%s' % (host, user, project))
            # else complain with an error!
        elif name.startswith('@'):
            new_specs.append(name)
        elif match:  # case 3 or 4
            user = match.group(1)
            project = match.group(2)
            for host in sorted(os.listdir(self.dir)):
                if host.startswith('.'):
                    continue
                user_dirname = os.path.join(self.dir, host, user)
                if project == 'all':  # case 4
                    if os.path.isdir(user_dirname):
                        for found_project in sorted(os.listdir(user_dirname)):
                            project_dirname = os.path.join(user_dirname,
                                                           found_project)
                            if not os.path.isdir(project_dirname):
                                continue
                            new_specs.append('%s/%s/%s' %
                                (host, user, found_project)
                            )
                else:  # case 3
                    project_dirname = os.path.join(
                        self.dir, host, user, project
                    )
                    if not os.path.isdir(project_dirname):
                        continue
                    new_specs.append('%s/%s/%s' % (host, user, project))
        elif '/' not in name:  # cases 5 and 6
            try:
                for host in os.listdir(self.dir):
                    if host.startswith('.'):
                        # skip hidden dirs
                        continue
                    host_dirname = os.path.join(self.dir, host)
                    for user in os.listdir(host_dirname):
                        user_dirname = os.path.join(host_dirname, user)
                        for project in os.listdir(user_dirname):
                            if project == name:
                                new_specs.append('%s/%s/%s' %
                                                 (host, user, project))
                            if (name.endswith('+') and
                                project.startswith(name[:-1])):
                                new_specs.append('%s/%s/%s' %
                                                 (host, user, project))
                                raise StopIteration
            except StopIteration:
                pass
        else:  # case 1 or 2
            components = name.split('/')
            host = components[0]
            user = ','.join(components[1:-1])
            project = components[-1]
            if project == 'all':  # case 2
                user_dirname = os.path.join(self.dir, host, user)
                for found_project in sorted(os.listdir(user_dirname)):
                    project_dirname = os.path.join(user_dirname, found_project)
                    if not os.path.isdir(project_dirname):
                        continue
                    new_specs.append('%s/%s/%s' % (host, user, found_project))
            else:  # case 1
                new_specs.append(name)

        return new_specs

    def expand_docked_specs(self, specs):
        """Convert a list of docked source specifiers into a list of
        expanded source specifiers.

        If any single docked source specificer does not resolve to
        any expanded source specifiers, an error is raised.

        If the option `unique` is given, an error is raised if the
        specs do not resolve to exactly one source.

        """
        if not specs:
            self.warn('No source specifiers given')
        new_specs = []
        for name in specs:
            additional_specs = self.expand_docked_spec(name)
            if not additional_specs:
                raise SourceSpecError(
                    "Docked spec '%s' didn't resolve to any Sources" % name
                )
            new_specs.extend(additional_specs)

        self.debug('Resolved source specs to %r' % new_specs)
        if self.options.unique and len(new_specs) != 1:
            raise SourceSpecError(
                "Could not resolve %s to a single unique source (%s)" % (
                    specs, new_specs
                )
            )
        return new_specs

    def make_source_from_spec(self, name):
        """Parse a single expanded source specifier and return a single
        Source object.

        An expanded source specifier may take any of the following forms:

          host/user/project          local source, already docked
          git://host.dom/.../user/repo.git       git
          http[s]://host.dom/.../user/repo.git   git
          http[s]://host.dom/.../user/repo       Mercurial
          http[s]://host.dom/.../distfile.tgz    \
          http[s]://host.dom/.../distfile.tar.gz | remotely hosted archive
          http[s]://host.dom/.../distfile.tar.xz | ("distfile" or "tarball")
          http[s]://host.dom/.../distfile.tar.bz2| (ftp:// also supported)
          http[s]://host.dom/.../distfile.zip    /
          path/to/.../distfile.tgz               \
          path/to/.../distfile.tar.gz            |
          path/to/.../distfile.tar.xz            | local distfile
          path/to/.../distfile.tar.bz2           |
          path/to/.../distfile.zip               /
          gh:user/project            short for https://github.com/...
          bb:user/project            short for https://bitbucket.org/...

        If problems are encountered while parsing the source spec,
        an exception will be raised.

        """
        tag = None
        match = re.match(r'^(.*?)\@(.*?)$', name)
        if match:
            name = match.group(1)
            tag = match.group(2)

        # resolve name shorthands
        # TODO: make these configurable
        match = re.match(r'^gh:(.*?)\/(.*?)$', name)
        if match:
            name = 'https://github.com/%s/%s.git' % (
                match.group(1), match.group(2)
            )
        match = re.match(r'^bb:(.*?)\/(.*?)$', name)
        if match:
            name = 'https://bitbucket.org/%s/%s' % (
                match.group(1), match.group(2)
            )

        match = re.match(r'^git:\/\/(.*?)/(.*?)/(.*?)\.git$', name)
        if match:
            host = match.group(1)
            user = match.group(2)
            project = match.group(3)
            return Source(self, url=name, host=host, user=user, project=project,
                          type='git', tag=tag)

        match = re.match(r'^https?:\/\/(.*?)/(.*?)/(.*?)\.git$', name)
        if match:
            host = match.group(1)
            user = match.group(2)
            project = match.group(3)
            return Source(self, url=name, host=host, user=user, project=project,
                          type='git', tag=tag)

        match = re.match(r'^(https?|ftp):\/\/(.*?)/.*?\/?([^/]*?)'
                         r'\.(zip|tgz|tar\.gz|tar\.xz|tar\.bz2)$', name)
        if match:
            host = match.group(2)
            project = match.group(3)
            ext = match.group(4)
            return Source(self, url=name, host=host, user='distfile',
                          project=project, type=ext, tag=tag)

        match = re.match(r'^https?:\/\/(.*?)/(.*?)/(.*?)\/?$', name)
        if match:
            host = match.group(1)
            user = match.group(2)
            project = match.group(3)
            return Source(self, url=name, host=host, user=user, project=project,
                          type='hg-or-git', tag=tag)

        # local distfile
        match = re.match(r'^(.*?\/)([^/]*?)\.(zip|tgz|tar\.gz|tar\.xz|tar\.bz2)$', name)
        if match:
            host = 'localhost'
            user = 'distfile'
            project = match.group(2)
            ext = match.group(3)
            # has "magic" filename?
            match = re.match(r'^([^,]*?),([^,]*?),([^,]*?)(\-[^\-]*?)?$', project)
            if match:
                host = match.group(1)
                user = match.group(2)
                project = match.group(3)
            return Source(self, url=name, host=host, user=user,
                          project=project, type=ext, local=True, tag=tag)

        # already docked
        match = re.match(r'^(.*?)\/(.*?)\/(.*?)$', name)
        if match:
            host = match.group(1)
            user = match.group(2)
            project = match.group(3)
            if os.path.isdir(os.path.join(self.dir, host, user, project)):
                # TODO divine type
                return Source(self, url='', host=host, user=user,
                              project=project, type='unknown', tag=tag)
            raise SourceSpecError("Source '%s' not docked" % name)

        raise SourceSpecError("Couldn't parse source spec '%s'" % name)

    def make_sources_from_specs(self, names):
        sources = []
        for name in names:
            try:
                sources += self.make_sources_from_spec(name)
            except Exception as e:
                if self.options.break_on_error:
                    raise
                self.errors.setdefault(name, []).append(str(e))
        return sources

    def make_sources_from_spec(self, name):
        """Parse an external source specifier and return a list of
        Source objects.

        An external source specifier may take any of the forms listed
        in make_source_from_spec's docstring, as well as the following:

          @local/file/name           read list of sources from file
          @@foo                      read list in .toolshelf/catalog/foo

        """
        if name.startswith('@@'):
            filename = os.path.join(
                self.dir, '.toolshelf', 'catalog', name[2:] + '.catalog'
            )
            return self.make_sources_from_catalog(filename)
        if name.startswith('@'):
            return self.make_sources_from_catalog(
                os.path.join(self.cwd, name[1:])
            )

        return [self.make_source_from_spec(name)]

    def make_sources_from_catalog(self, filename):
        self.debug('Reading catalog %s' % filename)
        sources = []
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if line == '' or line.startswith('#'):
                    continue
                sources += self.make_sources_from_spec(line)
        return sources

    ### processing sources ###

    def foreach_specced_source(self, specs, fun):
        """Call `fun` for each Source specified by the given specs.

        The working directory is changed to that Source's directory
        before `fun` is called.  (It is not changed back afterwards.)
        In addition, if `fun` raises an error, it will be caught and
        collected (unless the --break-on-error option was given.)

        Note that a single spec among the specs can result in
        multiple Sources.

        """
        sources = self.make_sources_from_specs(specs)
        for source in sources:
            if os.path.isdir(source.dir):
                self.chdir(source.dir)
            else:
                self.chdir(self.dir)
            try:
                fun(source)
            except Exception as e:
                if self.options.break_on_error:
                    raise
                self.errors.setdefault(source.name, []).append(str(e))

    def run_command(self, subcommand, args):
        # resolve @'s and @@'s which are given individually in the arglist
        new_args = []
        prefix = ''
        for arg in args:
            if prefix in ('@', '@@'):
                new_args.append(prefix + arg)
                prefix = ''
            elif arg in ('@', '@@'):
                prefix = arg
            else:
                new_args.append(arg)

        try:
            module = __import__("toolshelf.commands.%s" % subcommand,
                                fromlist=["toolshelf.commands"])
            cmd = lambda args: getattr(module, subcommand, None)(self, args)
        except ImportError:
            cmd = getattr(self, subcommand, None)
        if cmd is not None:
            try:
                cmd(new_args)
            except Exception as e:
                if self.options.break_on_error:
                    raise
                self.errors.setdefault(subcommand, []).append(str(e))
        else:
            module = __import__("toolshelf.commands.%s" % subcommand,
                                fromlist=["toolshelf.commands"])
            sys.stderr.write("Unrecognized subcommand '%s'\n" % subcommand)
            print "Usage: " + __doc__
            sys.exit(2)

    ### intrinsic subcommands ###

    def dock(self, args):
        def dock_it(source):
            if source.docked:
                print "%s already docked." % source.name
            else:
                require_executables = source.hints.get(
                    'require_executables', None
                )
                if require_executables:
                    p = Path()
                    for executable in require_executables.split(' '):
                        if not p.which(executable):
                            raise DependencyError(
                                '%s requires `%s` not found on search path' %
                                (source.name, executable)
                            )
                source.checkout()
                source.rectify_permissions_if_needed()
                source.build()
                source.relink()
        self.foreach_specced_source(args, dock_it)

    def tether(self, args):
        def tether_it(source):
            if source.docked:
                print "%s already docked." % source.name
            else:
                source.checkout()
        self.foreach_specced_source(args, tether_it)

    def build(self, args):
        def build_it(source):
            source.build()
            source.relink()
        self.foreach_specced_source(self.expand_docked_specs(args), build_it)

    def update(self, args):
        def update_it(source):
            was_changed = source.update()
            if was_changed:
                source.build()
                source.relink()
        self.foreach_specced_source(self.expand_docked_specs(args), update_it)

    def resolve(self, args):
        def dump_it(source):
            print repr(source)
        self.foreach_specced_source(self.expand_docked_specs(args), dump_it)

    def status(self, args):
        def status_it(source):
            source.status()
        self.foreach_specced_source(self.expand_docked_specs(args), status_it)

    def rectify(self, args):
        def rectify_it(source):
            source.rectify_executable_permissions()
        self.foreach_specced_source(self.expand_docked_specs(args), rectify_it)

    def relink(self, args):
        def relink_it(source):
            source.relink()
        self.foreach_specced_source(self.expand_docked_specs(args), relink_it)

    def disable(self, args):
        specs = self.expand_docked_specs(args)
        sources = self.make_sources_from_specs(specs)
        for source in sources:
            self.blacklist.add(source)
        self.relink(['all'])

    def enable(self, args):
        specs = self.expand_docked_specs(args)
        sources = self.make_sources_from_specs(specs)
        for source in sources:
            self.blacklist.remove(source)
        self.relink(args)

    def show(self, args):
        specs = self.expand_docked_specs(args)
        sources = self.make_sources_from_specs(specs)
        for source in sources:
            # TODO: colourize the output for which are exes, which are dirs
            for (link_farm_name, link_farm) in self.link_farms.iteritems():
                for (linkname, filename) in link_farm.links():
                    if filename.startswith(source.dir):
                        showname = filename.replace(self.dir, '$TOOLSHELF')
                        print "%s -> %s" % (os.path.basename(linkname), showname)
                        if link_farm is self.link_farms['bin']:
                            if (not os.path.isfile(filename) or
                                not os.access(filename, os.X_OK)):
                                print "BROKEN: %s is not an executable file" % filename


def main(args):
    parser = optparse.OptionParser(__doc__)

    parser.add_option("-B", "--no-build", dest="build",
                      default=True, action="store_false",
                      help="don't try to build sources during docking "
                           "and updating")
    parser.add_option("--debug", dest="debug",
                      default=False, action="store_true",
                      help="display messages to assist in troublshooting. "
                           "does not imply --verbose")
    parser.add_option("-f", "--force",
                      default=False, action="store_true",
                      help="subvert any safety mechanisms and just do "
                           "the thing regardless of the consequences")
    parser.add_option("--output-dir",
                      dest="output_dir", metavar='DIR',
                      default=os.path.realpath(os.path.abspath('.')),
                      help="for certain commands (release and export), "
                           "write the results into this directory "
                           "(default: %default)")
    parser.add_option("-K", "--break-on-error", dest="break_on_error",
                      default=False, action="store_true",
                      help="abort if error occurs with a single "
                           "source when processing multiple sources")
    parser.add_option("--login", dest="login",
                      default=None, metavar='USERNAME',
                      help="username to login with when using the "
                           "Github or Bitbucket APIs")
    parser.add_option("--unique", dest="unique",
                      default=False, action="store_true",
                      help="abort if given specs do not resolve to "
                           "exactly one source")
    parser.add_option("-q", "--quiet", dest="quiet",
                      default=False, action="store_true",
                      help="suppress output of warning messages")
    parser.add_option("-v", "--verbose", dest="verbose",
                      default=False, action="store_true",
                      help="report steps taken to standard output")

    (options, args) = parser.parse_args(args)
    if len(args) == 0:
        print "Usage: " + __doc__
        sys.exit(2)

    t = Toolshelf(options=options)

    t.run_command(args[0], args[1:])
    if t.errors:
        sys.stderr.write('\nERRORS:\n\n')
        for name in sorted(t.errors.keys()):
            sys.stderr.write(name + ':\n')
            for msg in t.errors[name]:
                sys.stderr.write(msg + '\n')
            sys.stderr.write('\n')
        sys.stderr.write('For usage, run `toolshelf --help`.\n')
        sys.exit(1)
    else:
        t.save()


if __name__ == '__main__':
    main(sys.argv[1:])
