#!/usr/bin/env python

# Copyright (c)2012 Chris Pressey, Cat's Eye Technologies
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

# Invoked by `toolshelf.sh` (for which `toolshelf` is an alias) to do the
# heavy lifting involved in docking packages and placing their relevant
# directories on the search path.

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
        Display the directories that are (or would be) put on your $PATH
        by the given docked sources.  Also show the executables in those
        directories.

    path check                                 (:not yet implemented:)
        Analyze the current $PATH and report any directories in it which are
        missing from the filesystem, and any executables on it which are
        shadowed by prior entries with the same name.

    path config <docked-source-spec>           (:not yet implemented:)
        Change the hints for a docked source.

    cd <docked-source-spec>
        Change the current working directory to the directory of the
        given docked source.

    consult <docked-source-spec>               (:not yet implemented:)
        Display a menu containing all files in the given docked source
        which are likely to be documentation; when one is selected,
        display its contents with $PAGER.
"""

import ConfigParser as configparser
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
    'build.pl', 'make.pl',
)

OPTIONS = None
CWD = os.getcwd()


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
    note("* Runnning `%s`..." % ' '.join(args))
    subprocess.check_call(args)


def note(msg):
    if OPTIONS.verbose:
        print msg


### Exceptions

class CommandLineSyntaxError(ValueError):
    pass


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


class Source(object):
    def __init__(self, url=None, host=None, user=None, project=None,
                       type=None, hints=''):
        self.url = url
        self.host = host
        self.user = user
        self.project = project
        self.type = type
        self.hints = hints
        self.subdir = self.user or self.host

    @classmethod
    def external_from_specs(klass, names):
        sources = []
        for name in names:
            sources += klass.external_from_spec(name)
        return sources

    @classmethod
    def external_from_spec(klass, name):
        """Parse an external source specifier and return a list of
        Source objects.

        An external source specifier may take any of the following forms:

          git://host.dom/.../user/repo.git       git
          http[s]://host.dom/.../user/repo.git   git
          http[s]://host.dom/.../user/repo       Mercurial
          http[s]://host.dom/.../distfile.tgz    |
          http[s]://host.dom/.../distfile.tar.gz | archive ("tarball")
          http[s]://host.dom/.../distfile.zip    |
          user/project           NYI use Preferences to guess
          @local/file/name           read list of sources from file
          @@foo                      read list in .toolshelf/catalog/foo

        A source specifier may also be followed by a hint set.
        A hint set is a colon-seperated list of hints enclosed in curly
        braces.  Example:

          user/project{x=tests:r=perl}

        """
        # TODO: should report warnings and errors

        # TODO: look up specifier in database, to obtain "cookies"

        hints = ''
        match = re.match(r'^(.*?)\{(.*?)\}$', name)
        if match:
            name = match.group(1)
            hints = match.group(2)

        match = re.match(r'^git:\/\/(.*?)/(.*?)/(.*?)\.git$', name)
        if match:
            host = match.group(1)
            user = match.group(2)
            project = match.group(3)
            return [
                Source(url=name, host=host, user=user, project=project,
                       type='git', hints=hints)
            ]

        match = re.match(r'^https?:\/\/(.*?)/(.*?)/(.*?)\.git$', name)
        if match:
            host = match.group(1)
            user = match.group(2)
            project = match.group(3)
            return [
                Source(url=name, host=host, user=user, project=project,
                       type='git', hints=hints)
            ]

        match = re.match(r'^https?:\/\/(.*?)/.*?\/?([^/]*?)\.(zip|tgz|tar\.gz)$', name)
        if match:
            host = match.group(1)
            project = match.group(2)
            ext = match.group(3)
            return [
                Source(url=name, host=host, project=project, type=ext,
                       hints=hints)
            ]

        match = re.match(r'^https?:\/\/(.*?)/(.*?)/(.*?)\/?$', name)
        if match:
            host = match.group(1)
            user = match.group(2)
            project = match.group(3)
            return [
                Source(url=name, host=host, user=user, project=project,
                       type='hg', hints=hints)
            ]

        match = re.match(r'^\@\@(.*?)$', name)
        if match:
            name = '@' + os.path.join(
                TOOLSHELF, '.toolshelf', 'catalog', name + '.catalog'
            )

        match = re.match(r'^\@(.*?)$', name)
        if match:
            sources = []
            filename = os.path.join(CWD, match.group(1))
            file = open(filename)
            for line in file:
                line = line.strip()
                if line == '' or line.startswith('#'):
                    continue
                sources += Source.external_from_spec(line)
            file.close()
            return sources

        match = re.match(r'^(.*?)\/(.*?)$', name)
        if match:
            user = match.group(1)
            project = match.group(2)
            # TODO: do we resolve this here, or upon checkout?
            return [
                Source(user=user, project=project, type='guess', hints=hints)
            ]

        return []

    @classmethod
    def docked_from_specs(klass, names):
        sources = []
        for name in names:
            sources += klass.docked_from_spec(name)
        return sources

    @classmethod
    def docked_from_spec(klass, name):
        """Parse a docked source specifier and return a list of Source
        objects.

        A docked source specifier may take any of the following forms:

          user/project               the source docked under this name
          user/*                 NYI all docked projects for this user
          *                          all docked projects
          project                NYI unambiguous project in toolshelf
          @local/file/name       NYI read list of sources from file
          @@foo                  NYI read list in toolshelf/catalog/foo

        """
        # TODO: should report warnings and errors
        # TODO: look up specifier in database, to obtain "cookies"

        if name == '*':
            # TODO: should divine whether a docked project is a git
            # repo, a mercurial repo, or whatnot.
            sources = []
            for user in os.listdir(TOOLSHELF):
                if user in ('.toolshelf', '.toolshelfrc'):
                    # skip the toolshelf dir itself
                    continue
                sub_dirname = os.path.join(TOOLSHELF, user)
                for project in os.listdir(sub_dirname):
                    project_dirname = os.path.join(sub_dirname, project)
                    if not os.path.isdir(project_dirname):
                        continue
                    # TODO: do we apply the given hints here?  (depends)
                    s = Source(user=user, project=project, type='unknown')
                    s.load_hints()
                    sources.append(s)
            return sources

        match = re.match(r'^(.*?)\/(.*?)$', name)
        if match:
            user = match.group(1)
            project = match.group(2)
            if os.path.isdir(os.path.join(TOOLSHELF, user, project)):
                s = Source(user=user, project=project, type='unknown')
                s.load_hints()
                return [s]
            return []

        return []

    @property
    def distfile(self):
        if self.type in ('zip', 'tgz', 'tar.gz'):
            return os.path.join(TOOLSHELF, self.subdir,
                                '%s.%s' % (self.project, self.type))
        else:
            return None

    @property
    def name(self):
        return os.path.join(self.subdir, self.project)

    @property
    def dir(self):
        return os.path.join(TOOLSHELF, self.name)

    def save_hints(self):
        filename = os.path.join(TOOLSHELF, '.toolshelfrc')
        config = configparser.RawConfigParser()
        config.read([filename])
        if not config.has_section('hints'):
            config.add_section('hints')
        config.set('hints', self.name, self.hints)
        f = open(filename, 'w')
        config.write(f)
        f.close()

    def load_hints(self):
        # TODO: it is inefficient to read this file every time
        filename = os.path.join(TOOLSHELF, '.toolshelfrc')
        config = configparser.RawConfigParser()
        config.read([filename])
        if not config.has_section('hints'):
            return
        try:
            self.hints = config.get('hints', self.name)
        except configparser.NoSectionError as e:
            return
        except configparser.NoOptionError as e:
            return            

    @property
    def docked(self):
        return os.path.isdir(self.dir)

    def checkout(self):
        note("* Checking out %s/%s..." % (self.subdir, self.project))

        os.chdir(TOOLSHELF)
        if not os.path.isdir(self.subdir):
            os.mkdir(self.subdir)
        os.chdir(self.subdir)

        if self.type == 'git':
            run('git', 'clone', self.url)
        elif self.type == 'hg':
            run('hg', 'clone', self.url)
        elif self.distfile is not None:
            run('rm', '-f', self.distfile)
            run('wget', '-nc', '-O', self.distfile, self.url)
            extract_dir = os.path.join(
                TOOLSHELF, self.subdir, '.extract_' + self.project
            )
            run('mkdir', '-p', extract_dir)
            os.chdir(extract_dir)
            if self.type == 'zip':
                run('unzip', self.distfile)
            elif self.type in ('tgz', 'tar.gz'):
                # TODO: use modern command line arguments to tar
                run('tar', 'zxvf', self.distfile)

            files = os.listdir(extract_dir)
            if len(files) == 1:
                extracted_dir = os.path.join(extract_dir, files[0])
                if not os.path.isdir(extracted_dir):
                    extracted_dir = extract_dir
            else:
                extracted_dir = extract_dir
            run('mv', extracted_dir, self.dir)
            run('rm', '-rf', extract_dir)

            if self.type == 'zip':
                self.rectify_executable_permissions()
        elif self.type == 'guess':
            # TODO: don't just assume it's on github
            run('git', 'clone', 'git://github.com/%s/%s.git' %
                (self.user, self.project))

        self.save_hints()

    def build(self):
        note("* Building %s/%s..." % (self.subdir, self.project))

        os.chdir(self.dir)
        if os.path.isfile('configure'):
            run('./configure')
        if os.path.isfile('Makefile'):
            run('make')
        elif os.path.isfile('src/Makefile'):
            os.chdir('src')
            run('make')
        elif os.path.isfile('build.sh'):
            run('./build.sh')

    def find_path_components(self):
        index = {}
        find_executables(self.dir, index)
        components = []
        for dirname in sorted(index):
            # TODO: rewrite this more elegantly
            add_it = True
            for hint in self.hints.split(':'):
                if hint.startswith('%'):
                    verboten = os.path.join(self.dir, hint[1:])
                    if dirname.startswith(verboten):
                        add_it = False
                        break
            if not add_it:
                note("(SKIPPING %s)" % dirname)
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
                        note("* Making %s executable" % name)
                        subprocess.check_call(["chmod", "u+x", filename])
                    else:
                        note("* Making %s NON-executable" % name)
                        subprocess.check_call(["chmod", "u-x", filename])

        traverse(self.dir)

### Subcommands

def dock_cmd(result, args):
    sources = Source.external_from_specs(args)
    for source in sources:
        source.checkout()
        source.build()
    path_cmd(result, ['rebuild'] + [s.name for s in sources])


def path_cmd(result, args):
    def clean_path(path, sources, all=False):
        # special case to handle total rebuilds/disables:
        if all:
            note("* Removing from your PATH all toolshelf directories")
            path.remove_components_by_prefix(TOOLSHELF)
        else:
            note("* Removing from your PATH all directories that start with one of the following...")
            for source in sources:
                note("  " + source.dir)
                path.remove_components_by_prefix(source.dir)

    if args[0] == 'rebuild':
        specs = args[1:]
        if not specs:
            specs = ['*']
        sources = Source.docked_from_specs(specs)
        p = Path()
        clean_path(p, sources, all=(specs == ['*']))
        note("* Adding the following executables to your PATH...")
        for source in sources:
            for component in source.find_path_components():
                p.add_component(component)
        p.write(result)
    elif args[0] == 'disable':
        specs = args[1:]
        if not specs:
            specs = ['*']
        sources = Source.docked_from_specs(specs)
        p = Path()
        clean_path(p, sources, all=(specs == ['*']))
        p.write(result)
    elif args[0] == 'show':
        # TODO: have this be meaningful even without --verbose
        specs = args[1:]
        if not specs:
            specs = ['*']
        sources = Source.docked_from_specs(specs)
        for source in sources:
            for component in source.find_path_components():
                pass
    else:
        raise CommandLineSyntaxError(
            "Unrecognized 'path' subcommand '%s'\n" % args[0]
        )


def cd_cmd(result, args):
    sources = Source.docked_from_specs(args)
    if len(sources) != 1:
        raise CommandLineSyntaxError(
            "'cd' subcommand requires exactly one source\n"
        )
    result.write('cd %s\n' % sources[0].dir)


SUBCOMMANDS = {
    'dock': dock_cmd,
    'path': path_cmd,
    'cd': cd_cmd,
}


if __name__ == '__main__':
    parser = optparse.OptionParser(__doc__)

    parser.add_option("-v", "--verbose", dest="verbose",
                      default=False, action="store_true",
                      help="report steps taken to standard output")

    (OPTIONS, args) = parser.parse_args()
    if len(args) == 0:
        print "Usage: " + __doc__
        sys.exit(2)

    os.chdir(TOOLSHELF)
    result = LazyFile(RESULT_SH_FILENAME)
    subcommand = args[0]
    if subcommand in SUBCOMMANDS:
        try:
            SUBCOMMANDS[subcommand](result, args[1:])
        except CommandLineSyntaxError as e:
            sys.stderr.write(str(e) + '\n')
            print "Usage: " + __doc__
            sys.exit(2)
        except subprocess.CalledProcessError as e:
            sys.stderr.write(str(e) + '\n')
            sys.exit(e.returncode)
    else:
        sys.stderr.write("Unrecognized subcommand '%s'\n" % subcommand)
        print "Usage: " + __doc__
        sys.exit(2)
    result.close()
