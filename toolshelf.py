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

# Invoked by the bash function `toolshelf()` to do the heavy lifting involved
# in docking packages and placing their relevant directories on the search
# path.

# Still largely under construction.

"""\
toolshelf {options} <subcommand>

Manage sources and paths maintained by the toolshelf environment.
Each <subcommand> has its own syntax.  <subcommand> is one of:

    dock {<external-source-spec>}
        Obtain source trees from a remote source, build executables for
        them as needed, and place those executables on your $PATH.
        Triggers a `path rebuild`.

    path rebuild {<docked-source-spec>}
        Update your $PATH to contain the executables for the given
        docked sources.  If none are given, all docked sources will apply.

    path disable {<docked-source-spec>}
        Temporarily remove the executables in the given docked projects
        from your $PATH.  A subsequent `path rebuild` will restore them.
        If no source specs are given, all docked sources will apply.

    path show {<docked-source-spec>}
        Display the directories that have been put on your $PATH by the
        given docked sources.  Also show the executables in those
        directories.

    path check                                 (:not yet implemented:)
        Analyze the current $PATH and report any directories in it which are
        missing from the filesystem, and any executables on it which are
        shadowed by prior entries with the same name.

    cd <docked-source-spec>
        Change the current working directory to the directory of the
        given docked source.

    consult <docked-source-spec>               (:not yet implemented:)
        Display a menu containing all files in the given docked source
        which are likely to be documentation; when one is selected,
        display its contents with $PAGER.
"""

import errno
import os
import optparse
import re
import subprocess
import sys


### Constants (per each run)

SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
TOOLSHELF = os.environ.get('TOOLSHELF')

RESULT_SH_FILENAME = os.path.join(TOOLSHELF, '.tmp-toolshelf-result.sh')

# TODO: these should be regexes
UNINTERESTING_EXECUTABLES = (
    'build.sh', 'make.sh', 'clean.sh', 'install.sh', 'test.sh',
    'build-cygwin.sh', 'make-cygwin.sh', 'install-cygwin.sh',
    'build.pl', 'make.pl', 'install.pl', 'test.pl',
    'configure', 'config.status',
)

HINT_NAMES = (
    'exclude_paths',
    'only_paths',
    'requires_executables',
    'prerequisites',
)

CWD = os.getcwd()


### Globals

OPTIONS = None
COOKIES = None


### Exceptions

class CommandLineSyntaxError(ValueError):
    pass


class SourceSpecError(ValueError):
    pass


### Helper Functions

def is_executable(filename):
    basename = os.path.basename(filename)
    if basename in UNINTERESTING_EXECUTABLES:
        return False
    return os.path.isfile(filename) and os.access(filename, os.X_OK)


def find_executables(dirname, index):
    for name in os.listdir(dirname):
        if name in ('.git', '.hg'):
            continue
        filename = os.path.join(dirname, name)
        if is_executable(filename):
            index.setdefault(dirname, []).append(name)
        elif os.path.isdir(filename):
            find_executables(filename, index)


def run(*args):
    note("Running `%s`..." % ' '.join(args))
    subprocess.check_call(args)


def chdir(path):
    note("Changing dir to `%s`..." % path)
    os.chdir(path)


def note(msg):
    if OPTIONS.verbose:
        print "*", msg


def expand_docked_specs(specs, default_all=False):
    """Convert a docked source specifier into a full source specifier.

    A docked source specifier may take any of the following forms:

      user/project           NYI from any host under this name
      project                    from any host & user under this name
      all                        all docked projects

    """
    if default_all and specs == []:
        specs = ['all']
    new_specs = []
    for name in specs:
        if name == 'all':
            for host in os.listdir(TOOLSHELF):
                if host.startswith('.'):
                    # skip hidden dirs
                    continue
                host_dirname = os.path.join(TOOLSHELF, host)
                for user in os.listdir(host_dirname):
                    sub_dirname = os.path.join(host_dirname, user)
                    for project in os.listdir(sub_dirname):
                        project_dirname = os.path.join(sub_dirname, project)
                        if not os.path.isdir(project_dirname):
                            continue
                        new_specs.append('%s/%s/%s' % (host, user, project))
        elif '/' not in name:
            found = False
            for host in os.listdir(TOOLSHELF):
                if found:
                    break
                if host.startswith('.'):
                    # skip hidden dirs
                    continue
                host_dirname = os.path.join(TOOLSHELF, host)
                for user in os.listdir(host_dirname):
                    if found:
                        break
                    sub_dirname = os.path.join(host_dirname, user)
                    for project in os.listdir(sub_dirname):
                        if project == name:
                            new_specs.append('%s/%s/%s' %
                                             (host, user, project))
                            found = True
                            break
        else:
            new_specs.append(name)

    return new_specs


def parse_source_spec(name):
    """Parse a full source specifier and return a dictionary
    of fields suitable for creating a Source object with.

    An full source specifier may take any of the following forms:

      host/user/project          local source, already docked
      git://host.dom/.../user/repo.git       git
      http[s]://host.dom/.../user/repo.git   git
      http[s]://host.dom/.../user/repo       Mercurial
      http[s]://host.dom/.../distfile.tgz    |
      http[s]://host.dom/.../distfile.tar.gz | archive ("tarball")
      http[s]://host.dom/.../distfile.zip    |
      gh:user/project            short for git://github.com/...
      bb:user/project            short for https://bitbucket.org/...

    If problems are encountered while parsing the source spec,
    an exception will be raised.

    """

    # resolve name shorthands
    # TODO: make these configurable
    match = re.match(r'^gh:(.*?)\/(.*?)$', name)
    if match:
        # TODO: allow different styles (https, git, ssh+git...)
        name = 'git://github.com/%s/%s.git' % (
            match.group(1), match.group(2)
        )
    match = re.match(r'^bb:(.*?)\/(.*?)$', name)
    if match:
        # TODO: allow different styles (https, git, ssh+git...)
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
                     r'\.(zip|tgz|tar\.gz)$', name)
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
                    type='hg')

    # local
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

class LazyFile(object):
    def __init__(self, filename):
        self.filename = filename
        self.file = None

    def write(self, data):
        if self.file is None:
            self.file = open(self.filename, 'w')
        self.file.write(data)

    def close(self):
        if self.file is not None:
            self.file.close()


class Cookies(object):
    def __init__(self):
        self.filename = os.path.join(
            TOOLSHELF, '.toolshelf', 'cookies.catalog'
        )
        self._hint_map = None

    def _load_hints(self):
        self._hint_map = {}
        with open(self.filename, 'r') as file:
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


class Source(object):
    def __init__(self, url=None, host=None, user=None, project=None,
                 type=None):
        self.url = url
        if not host:
            raise ValueError('no host supplied')
        self.host = host
        self.user = user or 'distfile'
        self.project = project
        self.type = type
        self.hints = {}
        COOKIES.apply_hints(self)

    def __repr__(self):
        return ("Source(url=%r, host=%r, user=%r, "
                "project=%r, type=%r, hints=%r)" %
                (self.url, self.host, self.user,
                 self.project, self.type, self.hints))

    @classmethod
    def from_catalog(klass, filename, problems):
        try:
            file = open(filename)
        except IOError as e:
            problems.append(e)
            return []
        sources = []
        for line in file:
            line = line.strip()
            if line == '' or line.startswith('#'):
                continue
            sources += Source.from_spec(line, problems)
        file.close()
        return sources

    @classmethod
    def from_specs(klass, names, problems):
        sources = []
        for name in names:
            sources += klass.from_spec(name, problems)
        return sources

    @classmethod
    def from_spec(klass, name, problems):
        """Parse an external source specifier and return a list of
        Source objects.

        An external source specifier may take any of the forms listed
        in parse_source_spec's docstring, as well as the following:

          @local/file/name           read list of sources from file
          @@foo                      read list in .toolshelf/catalog/foo

        If problems are encountered while parsing the source spec,
        they will be added to the problems parameter, assumed to be
        a list-like object.

        """
        if name.startswith('@@'):
            filename = os.path.join(
                TOOLSHELF, '.toolshelf', 'catalog', name[2:] + '.catalog'
            )
            return klass.from_catalog(filename, problems)
        if name.startswith('@'):
            return klass.from_catalog(name[1:], problems)

        try:
            kwargs = parse_source_spec(name)
            return [Source(**kwargs)]
        except Exception as e:
            problems.append(repr(e))
            return []

    @property
    def distfile(self):
        if self.type in ('zip', 'tgz', 'tar.gz'):
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

        try:
            os.makedirs(self.user_dir)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(self.user_dir):
                pass
            else:
                raise
        chdir(self.user_dir)

        if self.type == 'git':
            run('git', 'clone', self.url)
        elif self.type == 'hg':
            run('hg', 'clone', self.url)
        elif self.distfile is not None:
            run('mkdir', '-p', os.path.join(TOOLSHELF, '.distfiles'))
            if not os.path.exists(self.distfile):
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

            if self.type == 'zip':
                self.rectify_executable_permissions()
        else:
            raise NotImplementedError(self.type)

    def build(self):
        if not OPTIONS.build:
            note("SKIPPING build of %s" % self.name)
            return
        note("Building %s..." % self.dir)

        chdir(self.dir)
        if os.path.isfile('build.sh'):
            run('./build.sh')
        else:
            if os.path.isfile('autogen.sh'):
                run('./autogen.sh')
            if os.path.isfile('configure'):
                run('./configure')

            if os.path.isfile('Makefile'):
                run('make')
            elif os.path.isfile('src/Makefile'):
                chdir('src')
                run('make')

    def update(self):
        chdir(self.dir)
        if os.path.isdir('.git'):
            run('git', 'pull')
        if os.path.isdir('.hg'):
            run('hg', 'pull', '-u')
        else:
            raise NotImplementedError

    def may_use_path(self, dirname):
        exclude_paths = self.hints.get('exclude_paths', '').split(' ')
        if exclude_paths == ['']:
            return True
        for path in exclude_paths:
            verboten = os.path.join(self.dir, path)
            if dirname.startswith(verboten):
                return False
        return True

    def find_path_components(self):
        index = {}
        find_executables(self.dir, index)
        components = []
        for dirname in sorted(index):
            if not self.may_use_path(dirname):
                note("%s excluded from search path" % dirname)
                continue
            note("  %s:" % dirname)
            for filename in index[dirname]:
                note("    %s" % filename)
            components.append(dirname)
        return components

    def rectify_executable_permissions(self):
        def traverse(dirname):
            for name in os.listdir(dirname):
                if name in ('.git', '.hg'):
                    continue
                filename = os.path.join(dirname, name)
                if os.path.isdir(filename):
                    traverse(filename)
                else:
                    make_it_executable = False
                    pipe = subprocess.Popen(["file", filename],
                                            stdout=subprocess.PIPE)
                    output = pipe.communicate()[0]
                    if 'executable' in output:
                        make_it_executable = True
                    if make_it_executable:
                        note("Making %s executable" % name)
                        subprocess.check_call(["chmod", "u+x", filename])
                    else:
                        note("Making %s NON-executable" % name)
                        subprocess.check_call(["chmod", "u-x", filename])

        traverse(self.dir)


### Subcommands


def dock_cmd(result, args):
    problems = []
    sources = Source.from_specs(args, problems)
    # TODO: improve this
    if problems:
        raise SourceSpecError(repr(problems))
    for source in sources:
        # XXX for now, skip if already docked
        if not source.docked:
            source.checkout()
            source.build()
    path_cmd(result, ['rebuild'] + [s.name for s in sources])


def build_cmd(result, args):
    problems = []
    specs = expand_docked_specs(args)
    sources = Source.from_specs(specs, problems)
    # TODO: improve this
    if problems:
        raise SourceSpecError(repr(problems))
    for source in sources:
        source.build()
    path_cmd(result, ['rebuild'] + [s.name for s in sources])


def update_cmd(result, args):
    problems = []
    specs = expand_docked_specs(args)
    sources = Source.from_specs(specs, problems)
    # TODO: improve this
    if problems:
        raise SourceSpecError(repr(problems))
    for source in sources:
        source.update()
        source.build()
    path_cmd(result, ['rebuild'] + [s.name for s in sources])


def path_cmd(result, args):
    def clean_path(path, sources, all=False):
        # special case to handle total rebuilds/disables:
        # XXX all= no longer works, fix this somehow
        if all:
            note("Removing from your PATH all toolshelf directories")
            path.remove_components_by_prefix(TOOLSHELF)
        else:
            note("Removing from your PATH all directories that "
                 "start with one of the following...")
            for source in sources:
                note("  " + source.dir)
                path.remove_components_by_prefix(source.dir)

    if args[0] == 'rebuild':
        specs = expand_docked_specs(args[1:], default_all=True)
        problems = []
        sources = Source.from_specs(specs, problems)
        # TODO: improve this
        if problems:
            raise SourceSpecError(repr(problems))
        p = Path()
        clean_path(p, sources, all=(specs == ['all']))
        note("Adding the following executables to your PATH...")
        for source in sources:
            for component in source.find_path_components():
                p.add_component(component)
        p.write(result)
    elif args[0] == 'disable':
        specs = expand_docked_specs(args[1:], default_all=True)
        problems = []
        sources = Source.from_specs(specs, problems)
        # TODO: improve this
        if problems:
            raise SourceSpecError(repr(problems))
        p = Path()
        clean_path(p, sources, all=(specs == ['all']))
        p.write(result)
    elif args[0] == 'show':
        specs = expand_docked_specs(args[1:], default_all=True)
        problems = []
        sources = Source.from_specs(specs, problems)
        # TODO: improve this
        if problems:
            raise SourceSpecError(repr(problems))
        p = Path()
        for component in p.components:
            for source in sources:
                if component == source.dir or \
                   component.startswith(source.dir + '/'):
                    print component
                    for filename in sorted(os.listdir(component)):
                        if is_executable(os.path.join(component, filename)):
                            print "  %s" % filename
    else:
        raise CommandLineSyntaxError(
            "Unrecognized 'path' subcommand '%s'\n" % args[0]
        )


def cd_cmd(result, args):
    problems = []
    specs = expand_docked_specs(args)
    sources = Source.from_specs(specs, problems)
    # TODO: improve this
    if problems:
        raise SourceSpecError(repr(problems))
    if len(sources) != 1:
        raise CommandLineSyntaxError(
            "'cd' subcommand requires exactly one source\n"
        )
    result.write('cd %s\n' % sources[0].dir)


SUBCOMMANDS = {
    'dock': dock_cmd,
    'path': path_cmd,
    'cd': cd_cmd,
    'build': build_cmd,
    'update': update_cmd,
}


def main():
    global OPTIONS, COOKIES

    parser = optparse.OptionParser(__doc__)

    parser.add_option("-B", "--no-build", dest="build",
                      default=True, action="store_false",
                      help="don't try to build sources during docking")
    parser.add_option("-v", "--verbose", dest="verbose",
                      default=False, action="store_true",
                      help="report steps taken to standard output")

    (OPTIONS, args) = parser.parse_args()
    if len(args) == 0:
        print "Usage: " + __doc__
        sys.exit(2)

    chdir(TOOLSHELF)
    result = LazyFile(RESULT_SH_FILENAME)
    COOKIES = Cookies()

    subcommand = args[0]
    if subcommand in SUBCOMMANDS:
        try:
            SUBCOMMANDS[subcommand](result, args[1:])
        except CommandLineSyntaxError as e:
            sys.stderr.write(str(e) + '\n')
            print "Usage: " + __doc__
            sys.exit(2)
        except SourceSpecError as e:
            sys.stderr.write(repr(e) + '\n')
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            sys.stderr.write(str(e) + '\n')
            sys.exit(e.returncode)
    else:
        sys.stderr.write("Unrecognized subcommand '%s'\n" % subcommand)
        print "Usage: " + __doc__
        sys.exit(2)

    result.close()


if __name__ == '__main__':
    main()
