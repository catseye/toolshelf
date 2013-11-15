#!/usr/bin/env python

# Copyright (c)2012-2013 Chris Pressey, Cat's Eye Technologies
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
        farm which is on your executable search path.  Implies `build`.

    build {<docked-source-spec>}
        Build (or re-build) the executables for the given docked sources.

    update {<docked-source-spec>}
        Pull the latest revision of the given docked sources from each's
        upstream repository (which is always the external source from which
        it was originally docked.)  Implies `build`.  (But shouldn't.)

    status {<docked-source-spec>}
        Show the `hg status` or `git status`, as appropriate, in their
        naive format, for the given docked sources.

    relink {<docked-source-spec>}
        Update your link farm to contain links to the executables for the given
        docked sources.  If none are given, all docked sources will apply.

    disable {<docked-source-spec>}
        Temporarily remove the links to executables in the given docked projects
        from your link farm.  A subsequent `relink` will restore them.
        If no source specs are given, all docked sources will apply.

    show {<docked-source-spec>}
        Display the links that have been put on your linked farm for the
        given docked sources.  Also show the executables those links point to.
        Will also report any broken links and may, in the future, list any
        executables it shadows or is shadowed by.  (Pipe the output into grep
        to narrow this report down.  In fact, `ls -l $TOOLSHELF/.bin` will
        get you most of this information, when a colour listing is output,
        so it's tempting to just replace it with that...)

    pwd <docked-source-spec>
        Emit the name of the directory of the docked source (or exit with an
        error if there is no such source docked.)
    
    rectify {<docked-source-spec>}
        ...
    
    ghuser <login> <username>
        Create (on standard output) a catalog for all of the given Github user's
        repositories.  The login is either 'username:password', which is your
        Github login, not necessarily the target user's, and which is used to
        log in to the Github API, or 'none', in which the Github API will be
        used anonymously.  Note that this command is experimental and its
        syntax will likely change.
"""

import codecs
import errno
import os
import optparse
import re
import subprocess
import sys


__all__ = ['Toolshelf']


### Constants (per each run)

TOOLSHELF = os.environ.get('TOOLSHELF')

BIN_LINK_FARM_DIR = os.path.join(TOOLSHELF, '.bin')
LIB_LINK_FARM_DIR = os.path.join(TOOLSHELF, '.lib')

# TODO: these should be regexes
UNINTERESTING_EXECUTABLES = (
    'build.sh', 'make.sh', 'clean.sh', 'install.sh', 'test.sh',
    'build-cygwin.sh', 'make-cygwin.sh', 'install-cygwin.sh',
    'build.pl', 'make.pl', 'install.pl', 'test.pl',
    'configure', 'config.status', 'config.sub', 'config.guess',
    'missing', 'mkinstalldirs', 'install-sh', 'autogen.sh', 'ltmain.sh',
    '.gitignore', '__init__.py', 'setup.py',
    'Makefile', 'make-bindist.sh', 'index.html',
    'run', 'runme', 'buildme', 'compile',
    # these executables are not considered "interesting" because if you happen
    # to dock a source which builds an executable by one of these names and
    # toolshelf puts it on the path, you may just have a *wee* problem when
    # trying to build anything else after that point :)
    'make', 'ant', 'mkdir', 'mv', 'rm',
    'git', 'hg', 'wget','unzip', 'tar',
    'cat', 'which', 'install',
)

HINT_NAMES = (
    'build_command',
    'exclude_paths',
    'only_paths',
    #'prerequisites',
    'rectify_permissions',
    'require_executables',
)

CWD = os.getcwd()


### Globals

class DefaultOptions(object):
    break_on_error = True
    verbose = False
    build = True

# TODO: make not global (har)
OPTIONS = DefaultOptions()


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
    basename = os.path.basename(filename)
    if basename in UNINTERESTING_EXECUTABLES:
        return False
    if basename.endswith('.so'):
        return False
    return os.path.isfile(filename) and os.access(filename, os.X_OK)


def is_shared_object(filename):
    match = re.match('^.*?\.so$', filename)
    return os.path.isfile(filename) and match and os.access(filename, os.X_OK)


def run(*args, **kwargs):
    note("Running `%s`..." % ' '.join(args))
    subprocess.check_call(args, **kwargs)


def get_it(command):
    note("Running `%s`..." % command)
    output = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE
    ).communicate()[0]
    if OPTIONS.verbose:  # FIX
        print output
    return output


def chdir(dirname):
    note("Changing dir to `%s`..." % dirname)
    os.chdir(dirname)


def makedirs(dirname):
    try:
        os.makedirs(dirname)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(dirname):
            pass
        else:
            raise


def symlink(sourcename, linkname):
    note("Symlinking `%s` to `%s`..." % (linkname, sourcename))
    os.symlink(sourcename, linkname)


def note(msg):
    if OPTIONS.verbose:  # FIX
        print "*", msg


def expand_docked_specs(specs, default_all=False):
    """Convert a docked source specifier into a full source specifier.

    A docked source specifier may take any of the following forms:

    1. host/user/project          this particular host, user, project
    2. host/user/all              all docked projects by this user on this host
    3. user/project               from any host under this name
    4. user/all                   all docked projects by this user
    5. project                    from any host & user under this name
    6. proj+                      the first project found that starts w/'proj'
    7. all                        all docked projects

    """
    if default_all and specs == []:
        specs = ['all']
    new_specs = []
    for name in specs:
        match = re.match(r'^([^/]*)/([^/]*)$', name)
        if name == 'all':  # case 7
            for host in os.listdir(TOOLSHELF):
                if host.startswith('.'):
                    continue
                host_dirname = os.path.join(TOOLSHELF, host)
                for user in os.listdir(host_dirname):
                    user_dirname = os.path.join(host_dirname, user)
                    for project in os.listdir(user_dirname):
                        project_dirname = os.path.join(user_dirname, project)
                        if not os.path.isdir(project_dirname):
                            continue
                        new_specs.append('%s/%s/%s' % (host, user, project))
            break
        elif name.startswith('@'):
            new_specs.append(name)
        elif match:  # case 3 or 4
            user = match.group(1)
            project = match.group(2)
            for host in os.listdir(TOOLSHELF):
                if host.startswith('.'):
                    continue
                user_dirname = os.path.join(TOOLSHELF, host, user)
                if project == 'all':  # case 4
                    if os.path.isdir(user_dirname):
                        for project in os.listdir(user_dirname):
                            project_dirname = os.path.join(user_dirname, project)
                            if not os.path.isdir(project_dirname):
                                continue
                            new_specs.append('%s/%s/%s' % (host, user, project))            
                else:  # case 3
                    project_dirname = os.path.join(TOOLSHELF, host, user, project)
                    if not os.path.isdir(project_dirname):
                        continue
                    new_specs.append('%s/%s/%s' % (host, user, project))            
        elif '/' not in name:  # cases 5 and 6
            try:
                for host in os.listdir(TOOLSHELF):
                    if host.startswith('.'):
                        # skip hidden dirs
                        continue
                    host_dirname = os.path.join(TOOLSHELF, host)
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
            (host, user, project) = name.split('/')
            if project == 'all':  # case 2
                user_dirname = os.path.join(TOOLSHELF, host, user)
                for project in os.listdir(user_dirname):
                    project_dirname = os.path.join(user_dirname, project)
                    if not os.path.isdir(project_dirname):
                        continue
                    new_specs.append('%s/%s/%s' % (host, user, project))
            else:  # case 1
                new_specs.append(name)

    note('Resolved source specs to %r' % new_specs)
    return new_specs


def parse_source_spec(name):
    """Parse a full source specifier and return a dictionary
    of fields suitable for creating a Source object with.

    An full source specifier may take any of the following forms:

      host/user/project          local source, already docked
      git://host.dom/.../user/repo.git       git
      http[s]://host.dom/.../user/repo.git   git
      http[s]://host.dom/.../user/repo       Mercurial
      http[s]://host.dom/.../distfile.tgz    \
      http[s]://host.dom/.../distfile.tar.gz | remotely hosted archive
      http[s]://host.dom/.../distfile.tar.bz2| ("distfile" or "tarball")
      http[s]://host.dom/.../distfile.zip    /
      path/to/.../distfile.tgz               \
      path/to/.../distfile.tar.gz            | local distfile
      path/to/.../distfile.tar.bz2           |
      path/to/.../distfile.zip               /
      gh:user/project            short for git://github.com/...
      bb:user/project            short for https://bitbucket.org/...

    If problems are encountered while parsing the source spec,
    an exception will be raised.

    """

    # resolve name shorthands
    # TODO: make these configurable
    match = re.match(r'^gh:(.*?)\/(.*?)$', name)
    if match:
        name = 'git://github.com/%s/%s.git' % (
            match.group(1), match.group(2)
        )
    match = re.match(r'^ghh:(.*?)\/(.*?)$', name)
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
        return dict(url=name, host=host, user=user, project=project,
                    type='git')

    match = re.match(r'^https?:\/\/(.*?)/(.*?)/(.*?)\.git$', name)
    if match:
        host = match.group(1)
        user = match.group(2)
        project = match.group(3)
        return dict(url=name, host=host, user=user, project=project,
                    type='git')

    match = re.match(r'^https?:\/\/(.*?)/.*?\/?([^/]*?)'
                     r'\.(zip|tgz|tar\.gz|tar\.bz2)$', name)
    if match:
        host = match.group(1)
        project = match.group(2)
        ext = match.group(3)
        return dict(url=name, host=host, user='distfile', project=project,
                    type=ext)

    match = re.match(r'^https?:\/\/(.*?)/(.*?)/(.*?)\/?$', name)
    if match:
        host = match.group(1)
        user = match.group(2)
        project = match.group(3)
        return dict(url=name, host=host, user=user, project=project,
                    type='hg-or-git')

    # local distfile
    match = re.match(r'^(.*?\/)([^/]*?)\.(zip|tgz|tar\.gz|tar\.bz2)$', name)
    if match:
        host = match.group(1)
        project = match.group(2)
        ext = match.group(3)
        return dict(url=name, host='localhost', user='distfile',
                    project=project, type=ext, local=True)

    # already docked
    match = re.match(r'^(.*?)\/(.*?)\/(.*?)$', name)
    if match:
        host = match.group(1)
        user = match.group(2)
        project = match.group(3)
        if os.path.isdir(os.path.join(TOOLSHELF, host, user, project)):
            # TODO divine type
            return dict(url='', host=host, user=user, project=project,
                        type='unknown')
        raise SourceSpecError("Source '%s' not docked" % name)

    raise SourceSpecError("Couldn't parse source spec '%s'" % name)


### Classes

class Cookies(object):
    def __init__(self):
        self._hint_map = None
        self.filenames = []

    def add_file(self, filename):
        """Will not work after hints have been loaded.
        """
        if os.path.exists(filename):
            self.filenames.append(filename)

    def _load_hints(self):
        self._hint_map = {}
        for filename in self.filenames:
            self._load_hints_from_file(filename)

    def _load_hints_from_file(self, filename):
        with open(filename, 'r') as file:
            spec_key = None
            for line in file:
                line = line.strip()
                found_hint = False
                for hint_name in HINT_NAMES:
                    pattern = r'^%s\s+(.*?)\s*$' % hint_name
                    match = re.match(pattern, line)
                    if match:
                        if spec_key is None:
                            raise SourceSpecError(
                                'Found hint %s before any spec' % hint_name
                            )
                        hint_value = match.group(1)
                        note("Adding hint '%s %s' to %s" %
                            (hint_name, hint_value, spec_key)
                        )
                        self._hint_map[spec_key][hint_name] = hint_value
                        if (hint_name == 'rectify_permissions' and
                            hint_value not in ('yes', 'no')):
                            raise ValueError(
                                "rectify_permissions must be 'yes' or 'no'"
                            )
                        found_hint = True
                        break
                if found_hint or line == '' or line.startswith('#'):
                    continue
                spec = parse_source_spec(line)
                spec_key = os.path.join(
                    spec['host'], spec['user'], spec['project']
                )
                self._hint_map.setdefault(spec_key, {})

    @property
    def hint_map(self):
        if self._hint_map is None:
            self._load_hints()
        return self._hint_map

    def apply_hints(self, source):
        source.hints.update(self.hint_map.get(source.name, {}))


class Path(object):
    """For historical purposes only, although may still be used to
    see if executables shadow other executables in the search path.

    """
    def __init__(self, value=None):
        if value is None:
            value = os.environ['PATH']
        self.components = [dir.strip() for dir in value.split(':')]

    def write(self, result):
        value = ':'.join(self.components)
        result.write("export PATH='%s'\n" % value)

    def remove_components_by_prefix(self, prefix):
        self.components = [dir for dir in self.components
                           if not dir.startswith(prefix)]

    def add_component(self, dir):
        self.components.insert(0, dir)

    def which(self, filename):
        found = []
        for component in self.components:
            full_filename = os.path.join(component, filename)
            # TODO: this only looks for "interesting" executables...
            # should look for any
            if is_executable(full_filename):
                found.append(full_filename)
        return found


class LinkFarm(object):
    """A link farm is a directory which contains symbolic links
    to files (typically executables) in various other parts of
    the filesystem.

    """
    def __init__(self, dirname):
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
        filename = os.path.abspath(filename)
        filename = os.path.realpath(filename)
        linkname = os.path.basename(filename)
        linkname = os.path.join(self.dirname, linkname)
        if not os.path.islink(linkname):
            return None
        source = os.readlink(linkname)
        return (linkname, source)

    def create_link(self, filename):
        filename = os.path.abspath(filename)
        linkname = os.path.join(self.dirname, os.path.basename(filename))
        # We do trample existing links
        if os.path.islink(linkname):
            note("Trampling existing link %s" % linkname)
            os.unlink(linkname)
        symlink(filename, linkname)

    def clean(self, prefix=''):
        for (linkname, sourcename) in self.links():
            if sourcename.startswith(prefix):
                os.unlink(linkname)


class Source(object):
    def __init__(self, url=None, host=None, user=None, project=None,
                 type=None, local=False, cookies=None):
        self.url = url
        if not host:
            raise ValueError('no host supplied')
        self.host = host
        self.user = user or 'distfile'
        self.project = project
        self.type = type
        self.local = local
        self.hints = {}
        if not cookies:
            raise ValueError('no cookies given')
        if cookies:
            cookies.apply_hints(self)

    def __repr__(self):
        return ("Source(url=%r, host=%r, user=%r, "
                "project=%r, type=%r, local=%r, hints=%r)" %
                (self.url, self.host, self.user,
                 self.project, self.type, self.local, self.hints))

    @property
    def distfile(self):
        if self.type in ('zip', 'tgz', 'tar.gz', 'tar.bz2'):
            return os.path.join(TOOLSHELF, '.distfiles',
                                '%s.%s' % (self.project, self.type))
        else:
            return None

    @property
    def name(self):
        return os.path.join(self.host, self.user, self.project)

    @property
    def user_dir(self):
        return os.path.join(TOOLSHELF, self.host, self.user)

    @property
    def dir(self):
        return os.path.join(self.user_dir, self.project)

    @property
    def docked(self):
        return os.path.isdir(self.dir)

    def checkout(self):
        note("Checking out %s..." % self.name)

        makedirs(self.user_dir)
        chdir(self.user_dir)

        if self.type == 'git':
            run('git', 'clone', self.url)
        elif self.type == 'hg':
            run('hg', 'clone', self.url)
        elif self.type == 'hg-or-git':
            try:
                # better would be to check hg's error output for
                # 'Http Error 406'
                run('hg', 'clone', self.url)
            except subprocess.CalledProcessError:
                note("`hg clone` failed, so trying git")
                run('git', 'clone', self.url)
        elif self.distfile is not None:
            run('mkdir', '-p', os.path.join(TOOLSHELF, '.distfiles'))
            if not os.path.exists(self.distfile):
                if self.local:
                    run('cp', self.url, self.distfile)
                else:
                    run('wget', '-nc', '-O', self.distfile, self.url)
            extract_dir = os.path.join(
                TOOLSHELF, '.extract_' + self.project
            )
            run('mkdir', '-p', extract_dir)
            chdir(extract_dir)
            if self.type == 'zip':
                run('unzip', self.distfile)
            elif self.type in ('tgz', 'tar.gz'):
                # TODO: use modern command line arguments to tar
                run('tar', 'zxvf', self.distfile)
            elif self.type in ('tar.bz2'):
                # TODO: use modern command line arguments to tar
                run('tar', 'jxvf', self.distfile)

            files = os.listdir(extract_dir)
            if len(files) == 1:
                note("Archive is well-structured "
                     "(all files in one directory)")
                extracted_dir = os.path.join(extract_dir, files[0])
                if not os.path.isdir(extracted_dir):
                    extracted_dir = extract_dir
            else:
                note("Archive is a 'tarbomb' "
                     "(all files in the root of the archive)")
                extracted_dir = extract_dir
            run('mv', extracted_dir, self.dir)
            run('rm', '-rf', extract_dir)
        else:
            raise NotImplementedError(self.type)

    def build(self):
        if not OPTIONS.build:  # FIX
            note("SKIPPING build of %s" % self.name)
            return
        note("Building %s..." % self.dir)

        chdir(self.dir)
        build_command = self.hints.get('build_command', None)
        if build_command:
            run(build_command, shell=True)
        elif os.path.isfile('build.sh'):
            run('./build.sh')
        elif os.path.isfile('make.sh'):
            run('./make.sh')
        elif os.path.isfile('build.xml'):
            run('ant')
        else:
            if (os.path.isfile('autogen.sh') and
                not os.path.isfile('configure')):
                run('./autogen.sh')
            if os.path.isfile('configure'):
                run('./configure', "--prefix=%s" % self.dir)
                run('make')
                run('make', 'install')
            elif os.path.isfile('Makefile') or os.path.isfile('makefile'):
                run('make')
            elif os.path.isfile('src/Makefile'):
                chdir('src')
                run('make')

    def update(self):
        chdir(self.dir)
        if os.path.isdir('.git'):
            run('git', 'pull')
        elif os.path.isdir('.hg'):
            run('hg', 'pull', '-u')
        else:
            raise NotImplementedError

    def status(self):
        chdir(self.dir)
        output = None
        if os.path.isdir('.git'):
            output = get_it('git status')
            if 'working directory clean' in output:
                output = ''
        elif os.path.isdir('.hg'):
            output = get_it('hg status')
        if output:
            print self.dir
            print output

    def may_use_path(self, dirname):
        only_paths = self.hints.get('only_paths', None)
        if only_paths:
            only_paths = only_paths.split(' ')
            for path in only_paths:
                if dirname == os.path.join(self.dir, path):
                    return True
            return False
        exclude_paths = self.hints.get('exclude_paths', None)
        if exclude_paths:
            exclude_paths = exclude_paths.split(' ')
            for path in exclude_paths:
                verboten = os.path.join(self.dir, path)
                if dirname.startswith(verboten):
                    return False
        return True

    def linkable_files(self, predicate):
        for root, dirs, files in os.walk(self.dir):
            if '.git' in dirs:
                dirs.remove('.git')
            if '.hg' in dirs:
                dirs.remove('.hg')
            if not self.may_use_path(root):
                note("%s excluded from search path" % root)
                dirs[:] = []
                continue
            for name in files:
                filename = os.path.join(self.dir, root, name)
                if predicate(filename):
                    note("    %s" % filename)
                    yield filename

    def rectify_executable_permissions(self):
        for root, dirs, files in os.walk(self.dir):
            if '.git' in dirs:
                dirs.remove('.git')
            if '.hg' in dirs:
                dirs.remove('.hg')
            for name in files:
                filename = os.path.join(self.dir, root, name)
                make_it_executable = False
                pipe = subprocess.Popen(["file", filename],
                                        stdout=subprocess.PIPE)
                output = pipe.communicate()[0]
                if 'executable' in output:
                    make_it_executable = True
                if make_it_executable:
                    note("Making %s executable" % filename)
                    subprocess.check_call(["chmod", "u+x", filename])
                else:
                    note("Making %s NON-executable" % filename)
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
        cwd = os.getcwd()
        os.chdir(self.dir)
    
        latest_tag = None
        for line in get_it("hg tags").split('\n'):
            match = re.match(r'^\s*(\S+)\s+(\d+):(.*?)\s*$', line)
            if match:
                tag = match.group(1)
                tags[tag] = int(match.group(2))
                if tag != 'tip' and latest_tag is None:
                    latest_tag = tag

        os.chdir(cwd)
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


### Toolshelf object (Subcommands)


class Toolshelf(object):
    def __init__(self, options=DefaultOptions(), cookies=None,
                       bin_link_farm=LinkFarm(BIN_LINK_FARM_DIR),
                       lib_link_farm=LinkFarm(LIB_LINK_FARM_DIR),
                       errors=None):
        self.options = options
        if cookies is None:
            cookies = Cookies()
            cookies.add_file(os.path.join(
                TOOLSHELF, '.toolshelf', 'cookies.catalog'
            ))
            cookies.add_file(os.path.join(
                TOOLSHELF, '.toolshelf', 'local-cookies.catalog'
            ))
        self.cookies = cookies
        self.bin_link_farm = bin_link_farm
        self.lib_link_farm = lib_link_farm
        if errors is None:
            errors = {}
        self.errors = errors

    def make_sources_from_catalog(self, filename):
        note('Reading catalog %s' % filename)
        sources = []
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if line == '' or line.startswith('#'):
                    continue
                sources += self.make_sources_from_spec(line)
        return sources

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
        in parse_source_spec's docstring, as well as the following:

          @local/file/name           read list of sources from file
          @@foo                      read list in .toolshelf/catalog/foo

        """
        if name.startswith('@@'):
            filename = os.path.join(
                TOOLSHELF, '.toolshelf', 'catalog', name[2:] + '.catalog'
            )
            return self.make_sources_from_catalog(filename)
        if name.startswith('@'):
            return self.make_sources_from_catalog(os.path.join(CWD, name[1:]))

        kwargs = parse_source_spec(name)
        kwargs['cookies'] = self.cookies
        return [Source(**kwargs)]

    def foreach_source(self, specs, fun, rebuild_paths=True):
        cwd = os.getcwd()
        sources = self.make_sources_from_specs(specs)
        for source in sorted(sources, key=str):
            if os.path.isdir(source.dir):
                os.chdir(source.dir)
            else:
                os.chdir(TOOLSHELF)
            try:
                fun(source)
            except Exception as e:
                if self.options.break_on_error:
                    raise
                self.errors.setdefault(source.name, []).append(str(e))
            finally:
                os.chdir(cwd)
        if rebuild_paths:
            self.relink([s.name for s in sources])

    def run_command(self, subcommand, args):
        cmd = getattr(self, subcommand, None)
        if cmd is not None:
            try:
                cmd(args)
            except Exception as e:
                if self.options.break_on_error:
                    raise
                self.errors.setdefault(subcommand, []).append(str(e))
        else:
            sys.stderr.write("Unrecognized subcommand '%s'\n" % subcommand)
            print "Usage: " + __doc__
            sys.exit(2)

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
        self.foreach_source(args, dock_it)
    
    def build(self, args):
        self.foreach_source(
            expand_docked_specs(args), lambda(source): source.build()
        )
    
    def update(self, args):
        def update(source):
            source.update()
            source.build()
        self.foreach_source(expand_docked_specs(args), update)

    def status(self, args):
        self.foreach_source(
            expand_docked_specs(args), lambda(source): source.status()
        )

    def pwd(self, args):
        specs = expand_docked_specs(args)
        sources = self.make_sources_from_specs(specs)
        if len(sources) != 1:
            raise SourceSpecError(
                "Could not resolve %s to a single unique source (%s)" % (
                    args, [s.dir for s in sources]
                )
            )
        print sources[0].dir
    
    def rectify(self, args):
        specs = expand_docked_specs(args)
        sources = self.make_sources_from_specs(specs)
        for source in sources:
            source.rectify_permissions_if_needed()
    
    def relink(self, args):
        specs = expand_docked_specs(args, default_all=True)
        sources = self.make_sources_from_specs(specs)
        note("Adding the following executables to your link farm...")
        for source in sources:
            self.bin_link_farm.clean(prefix=source.dir)
            for filename in source.linkable_files(is_executable):
                self.bin_link_farm.create_link(filename)
            self.lib_link_farm.clean(prefix=source.dir)
            for filename in source.linkable_files(is_shared_object):
                self.lib_link_farm.create_link(filename)
    
    def disable(self, args):
        specs = expand_docked_specs(args, default_all=True)
        sources = self.make_sources_from_specs(specs)
        for source in sources:
            self.bin_link_farm.clean(prefix=source.dir)
            self.lib_link_farm.clean(prefix=source.dir)
    
    def show(self, args):
        specs = expand_docked_specs(args, default_all=True)
        sources = self.make_sources_from_specs(specs)
        for source in sources:
            for (linkname, filename) in self.link_farm.links():
                if filename.startswith(source.dir):
                    print "%s -> %s" % (os.path.basename(linkname), filename)
                    if (not os.path.isfile(filename) or
                        not os.access(filename, os.X_OK)):
                        print "BROKEN: %s is not an executable file" % filename
    
    def ghuser(self, args):
        import requests
        login = args[0]
        user = args[1]
        if login == 'none':
            login = ''
        else:
            login = login + '@'
        url = 'https://%sapi.github.com/users/%s/repos' % (login, user)
        
        done = False
        while not done:
            response = requests.get(url)
            data = response.json()
            for x in data:
                print 'gh:%s' % x['full_name']
            link = response.headers.get('Link', None)
            if link is None:
                done = True
            else:
                match = re.match(r'\<(.*?)\>\s*\;\s*rel\s*=\s*\"next\"', link)
                if not match:
                    note(link)
                    done = True
                else:
                    url = match.group(1)
    
    def bbuser(self, args):
        # this only works for the logged-in user.  It would be great if...
        # yeah.
        from bitbucket.bitbucket import Bitbucket
        (username, password) = args[0].split(':')
        bb = Bitbucket(username, password)
        success, repositories = bb.repository.all()
        for repo in sorted(repositories):
            print 'bb:%s/%s' % (username, repo['slug'])
    
    def release(self, args):
        """Create a distfile from the latest tag in a local version-controlled
        source tree.
        
        """
        cwd = os.getcwd()
        specs = expand_docked_specs(args, default_all=False)
        sources = self.make_sources_from_specs(specs)
        for source in sources:
            distro = source.project
            tag = source.get_latest_release_tag()
            if not tag:
                raise SystemError("Repository not tagged")
            os.chdir(source.dir)
            diff = get_it('hg diff -r %s -r tip -X .hgtags' % tag)
            if diff and not self.options.force:
                raise SystemError("There are changes to mainline since latest tag")
            os.chdir(cwd)
    
            match = re.match(r'^rel_(\d+)_(\d+)_(\d+)_(\d+)$', tag)
            if match:
                v_maj = match.group(1)
                v_min = match.group(2)
                r_maj = match.group(3)
                r_min = match.group(4)
                filename = '%s-%s.%s-%s.%s.zip' % (
                    distro, v_maj, v_min, r_maj, r_min
                )
            else:
                match = re.match(r'^rel_(\d+)_(\d+)$', tag)
                if match:
                    v_maj = match.group(1)
                    v_min = match.group(2)
                    r_maj = "0"
                    r_min = "0"
                    filename = '%s-%s.%s.zip' % (distro, v_maj, v_min)
                else:
                    raise ValueError("Not a release tag that I understand: %s" % tag)
            print """\
  - version: "%s.%s"
    revision: "%s.%s"
    url: http://catseye.tc/distfiles/%s
""" % (v_maj, v_min, r_maj, r_min, filename)
            full_filename = os.path.join(self.options.distfiles_dir, filename)
            if os.path.exists(full_filename):
                run('unzip', '-v', full_filename)
                raise SystemError("Distfile already exists: %s" % full_filename)
            command = ['hg', 'archive', '-t', 'zip', '-r', tag]
            for x in ('.hgignore', '.gitignore',
                      '.hgtags', '.hg_archival.txt'):
                command.append('-X')
                command.append(x)
            command.append(full_filename)
            os.chdir(source.dir)
            run(*command)
            os.chdir(cwd)
            run('unzip', '-v', full_filename)
    
    def lint(self, args):
        """Check that the layouts of distributions conform to some
        distribution organization guidelines.  If these are not guidelines that
        you use, you can take this with a grain of salt.
    
        """
        problems = {}
    
        OK_ROOT_FILES = (
            'LICENSE', 'UNLICENSE',
            'README.markdown', 'TODO.markdown', 'HISTORY.markdown',
            'test.sh', 'clean.sh',
            'make.sh', 'make-cygwin.sh', 'Makefile',
            '.hgtags', '.hgignore', '.gitignore',
        )
        OK_ROOT_DIRS = (
            'bin', 'contrib', 'demo', 'dialect',
            'disk', 'doc', 'ebin', 'eg', 'images',
            'impl', 'lib', 'priv', 'script',
            'src', 'tests',
            '.hg',
        )
    
        def lint_it(source):
            prob = []
            if not os.path.exists('README.markdown'):
                prob.append("No README.markdown")
            if not os.path.exists('LICENSE') and not os.path.exists('UNLICENSE'):
                prob.append("No LICENSE or UNLICENSE")
            if os.path.exists('LICENSE') and os.path.exists('UNLICENSE'):
                prob.append("Both LICENSE and UNLICENSE")
            for root, dirnames, filenames in os.walk('.'):
                if root.endswith(".hg"):
                    del dirnames[:]
                    continue
                if root == '.':
                    root_files = []
                    for filename in filenames:
                        if filename not in OK_ROOT_FILES:
                            root_files.append(filename)
                    if root_files:
                        prob.append(
                            "Junk files in root: %s" % root_files
                        )
    
                    root_dirs = []
                    for dirname in dirnames:
                        if dirname not in OK_ROOT_DIRS:
                            root_dirs.append(dirname)
                    if root_dirs:
                        prob.append(
                            "Junk dirs in root: %s" % root_dirs
                        )
            problems[source.dir] = prob
    
        self.foreach_source(
            expand_docked_specs(args), lint_it,
            rebuild_paths=False
        )

        problematic_count = 0
        for d in sorted(problems.keys()):
            if not problems[d]:
                continue
            print d
            print '-' * len(d)
            print
            for problem in problems[d]:
                print "* %s" % problem
            print
            problematic_count += 1
    
        #print "Linted %d clones, problems in %d of them." % (
        #    count, problematic_count
        #)
    
    def survey(self, args):
        """Generates a report summarizing various properties of the docked
        source trees.  Sort of a "deep status".
    
        """
        repos = {}
    
        def survey_it(source):
            print source.name
            dirty = get_it("hg st")
            outgoing = ''
            #if hg_outgoing:
            #    outgoing = get_it("hg out")
            #if 'no changes found' in outgoing:
            #    outgoing = ''
            tags = {}
            latest_tag = source.get_latest_release_tag(tags)
            due = ''
            diff = ''
            if latest_tag is None:
                due = 'NEVER RELEASED'
            else:
                diff = get_it('hg diff -r %s -r tip -X .hgtags' % latest_tag)
                if not diff:
                    due = ''
                else:
                    due = "%d changesets (tip=%d, %s=%d)" % \
                        ((tags['tip'] - tags[latest_tag]), tags['tip'],
                         latest_tag, tags[latest_tag])
            repos[source.name] = {
                'dirty': dirty,
                'outgoing': outgoing,
                'tags': tags,
                'latest_tag': latest_tag,
                'due': due,
                'diff': diff,
            }
    
        self.foreach_source(
            expand_docked_specs(args), survey_it,
            rebuild_paths=False
        )

        print '-----'
        for repo in sorted(repos.keys()):
            r = repos[repo]
            if r['dirty'] or r['outgoing'] or r['due']:
                print repo
                if r['dirty']:
                    print r['dirty']
                if r['outgoing']:
                    print r['outgoing']
                if r['due']:
                    print "  DUE:", r['due']
                print
        print '-----'

    def test(self, args):
        stats = {
            'sources': 0,
            'no_tests': 0,
            'passes': [],
            'fails': []
        }
        def test_it(source):
            stats['sources'] += 1
            if os.path.exists(os.path.join(source.dir, 'test.sh')):
                process = subprocess.Popen(
                    './test.sh', shell=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                (std_output, std_error) = process.communicate()
                if self.options.verbose:
                    sys.stdout.write(std_output)
                    sys.stdout.write(std_error)
                if process.returncode == 0:
                    stats['passes'].append(source)
                else:
                    stats['fails'].append(source)
            else:
                stats['no_tests'] += 1
    
        self.foreach_source(
            expand_docked_specs(args), test_it,
            rebuild_paths=False
        )
        
        print "Total docked sources tested:   %s" % stats['sources']
        print "Total without obvious tests:   %s" % stats['no_tests']
        print "Total passing:                 %s" % len(stats['passes'])
        if self.options.verbose:
            print [s.name for s in stats['passes']]
        print "Total failures:                %s" % len(stats['fails'])
        if self.options.verbose:
            print [s.name for s in stats['fails']]

    def collectdocs(self, args):
        """Looks for documentation in local repository clones and writes out
        a files that can be used to update the Documentation nodes in the
        Chrysoberyl data.
    
        """
        import yaml
        docdict = {}
    
        def collectdocs_it(source):
            for path in source.find_likely_documents():
                docdict.setdefault(source.name, []).append(path)
    
        self.foreach_source(
            expand_docked_specs(args), collectdocs_it
        )
    
        output_filename = 'docs.yaml'
        with codecs.open(output_filename, 'w', 'utf-8') as file:
            file.write('# encoding: UTF-8\n')
            file.write('# AUTOMATICALLY GENERATED BY chrysoberyl.py\n')
            file.write(yaml.dump(docdict, Dumper=yaml.Dumper, default_flow_style=False))


def main(args):
    global OPTIONS

    parser = optparse.OptionParser(__doc__)

    parser.add_option("-B", "--no-build", dest="build",
                      default=True, action="store_false",
                      help="don't try to build sources during docking")
    parser.add_option("-f", "--force",
                      default=False, action="store_true",
                      help="subvert any safety mechanisms and just do "
                           "the thing regardless of the consequences")
    parser.add_option("--distfiles-dir",
                      dest="distfiles_dir", metavar='DIR',
                      default='../catseye_tc/catseye.tc/distfiles',
                      help="write distfiles into this directory "
                           "(default: %default)")
    parser.add_option("-K", "--break-on-error", dest="break_on_error",
                      default=False, action="store_true",
                      help="abort if error occurs with a single "
                           "source when processing multiple sources")
    parser.add_option("-v", "--verbose", dest="verbose",
                      default=False, action="store_true",
                      help="report steps taken to standard output")

    (OPTIONS, args) = parser.parse_args(args)
    if len(args) == 0:
        print "Usage: " + __doc__
        sys.exit(2)

    t = Toolshelf(options=OPTIONS)

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


if __name__ == '__main__':
    main(sys.argv[1:])
