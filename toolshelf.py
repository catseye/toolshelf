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

Manage projects, sources, and paths maintained by the toolshelf environment.

<subcommand> is one of:

    dock <prj>    - obtain project sources from a website and place on path
    path rebuild  - update your PATH env var to reflect all docked projects
"""

import os
import re
import sys
from optparse import OptionParser


### Constants (per each run)

SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
# TODO: maybe this should not default to the .. of the script dir if env var isn't there?
TOOLSHELF = os.environ.get('TOOLSHELF', os.path.join(SCRIPT_DIR, '..'))

RESULT_SH_FILENAME = os.path.join(SCRIPT_DIR, 'tmp-toolshelf-result.sh')

UNINTERESTING_EXECUTABLES = (
    'build.sh', 'make.sh', 'clean.sh', 'install.sh'
)

OPTIONS = None

### Helper Functions

def is_executable(filename):
    basename = os.path.basename(filename)
    if basename in UNINTERESTING_EXECUTABLES:
        return False
    return os.path.isfile(filename) and os.access(filename, os.X_OK)


def list_executables(dirname):
    executables = []
    for name in os.listdir(dirname):
        filename = os.path.join(dirname, name)
        if is_executable(filename):
            executables.append(filename)
    return executables


def find_executables(dirname, index):
    for name in os.listdir(dirname):
        filename = os.path.join(dirname, name)
        if is_executable(filename):
            index.setdetfault(dirname, []).append(name)
        elif os.path.isdir(filename):
            find_executables(filename, index)


def compute_toolshelf_path(dirnames):
    index = {}
    for dirname in dirnames:
        find_executables(dirname, index)
    components = []
    for dirname in index:
        if OPTIONS.verbose:
            print "%s:" % dirname
            for filename in index[dirname]:
                print "  %s" % filename
        components.append(dirname)
    return components


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

    def remove_toolshelf_components(self):
        self.components = [dir for dir in self.components
                           if not dir.startswith(TOOLSHELF)]

    def add_toolshelf_components(self):
        # TODO: this is the old way, remove it
        for name in os.listdir(TOOLSHELF):
            if name == 'toolshelf':
                # skip the toolshelf dir itself
                continue
            user_dir_name = os.path.join(TOOLSHELF, name)
            for name in os.listdir(user_dir_name):
                project_dir_name = os.path.join(user_dir_name, name)
                if not os.path.isdir(project_dir_name):
                    continue
                for candidate in ('bin', 'script', 'scripts'):
                    bin_dir_name = os.path.join(project_dir_name, candidate)
                    if os.path.isdir(bin_dir_name):
                        print bin_dir_name
                        self.components.append(bin_dir_name)
                # If there are any executable files in the project's root
                # directory, add it to the path, too.  Note, this does
                # generate some false positives; maybe we should be a
                # little less cavalier (or more clever) about this.
                add_project_root_to_path = False
                for name in os.listdir(project_dir_name):
                    project_filename = os.path.join(project_dir_name, name)
                    if (os.path.isfile(project_filename) and
                        os.access(project_filename, os.X_OK)):
                        add_project_root_to_path = True
                        break
                if add_project_root_to_path:
                    print project_dir_name
                    self.components.append(project_dir_name)

    def add_components_from_sources(self, sources):
        self.components += compute_toolshelf_path([s.dir for s in sources])


class Source(object):
    def __init__(self, url=None, host=None, user=None, project=None, type=None):
        self.url = url
        self.host = host
        self.user = user
        self.project = project
        self.type = type
        self.subdir = self.user or self.host

    @classmethod
    def load_docked(name, exists=False):
        """Return a list of Source objects representing all sources
        currently docked.
        """
        # TODO: should divine whether a docked project is a git
        # repo, a mercurial repo, or whatnot.  Should probably
        # call parse_spec with exists=True for this, and that should
        # be responsible for it.

        specs = []
        for user in os.listdir(TOOLSHELF):
            if user == 'toolshelf':
                # skip the toolshelf dir itself
                continue
            sub_dirname = os.path.join(TOOLSHELF, user)
            for project in os.listdir(sub_dirname):
                project_dirname = os.path.join(sub_dirname, project)
                if not os.path.isdir(project_dirname):
                    continue
                specs.add(Source(user=user, project=project, type='unknown'))

    @classmethod
    def parse_spec(klass, name, exists=False):
        """Parse a source specifier and return a list of Source objects.

        A source specifier may take any of the following forms:

          git://host.dom/.../user/repo.git       git
          http[s]://host.dom/.../user/repo.git   git
          http[s]://host.dom/.../user/repo       Mercurial
          http[s]://host.dom/.../distfile.tgz    (or .tar.gz) tarball
          http[s]://host.dom/.../distfile.zip    zipball
          user/repo                  use Preferences to guess
          @local/file/name           read list of specs from file
          @@foo                      read list in toolshelf/catalog/foo
          repo                       unambiguous repo in toolshelf (exists=True only)

        """
        # TODO: should report warnings and errors

        # TODO: look up specifier in database, to obtain "cookies"

        specs = []

        match = re.match(r'^git:\/\/(.*?)/(.*?)/(.*?).git$', name)
        if match:
            host = match.group(1)
            user = match.group(2)
            project = match.group(3)
            specs.append(Source(url=name, host=host, user=user, project=project, type='git'))
        match = re.match(r'^https?:\/\/(.*?)/(.*?)/(.*?).git$', name)
        if match:
            host = match.group(1)
            user = match.group(2)
            project = match.group(3)
            specs.append(Source(url=name, host=host, user=user, project=project, type='git'))

        match = re.match(r'^https?:\/\/(.*?)/(.*?)/(.*?)\/?$', name)
        if match:
            host = match.group(1)
            user = match.group(2)
            project = match.group(3)
            specs.append(Source(url=name, host=host, user=user, project=project, type='hg'))

        match = re.match(r'^(.*?)\/(.*?)$', name)
        if match:
            user = match.group(1)
            project = match.group(2)
            specs.append(Source(user=user, project=project, type='guess'))

        match = re.match(r'^\@(.*?)$', name)
        if match:
            filename = match.group(1)
            file = open(filename)
            for line in file:
               specs += parse_source_spec(line, exists=exists)
            file.close()

        return specs

    @property
    def dir(self):
        return os.path.join(TOOLSHELF, self.subdir, self.project)

    @property
    def docked(self):
        return os.path.isdir(self.dir)

    def checkout(self):
        if OPTIONS.verbose:
            print "Checking out %s/%s..." % (self.subdir, self.project)

        os.chdir(TOOLSHELF)
        if not os.path.isdir(self.subdir):
            os.mkdir(self.subdir)
        os.chdir(self.subdir)

        if self.type == 'git':
            exit_code = os.system('git clone %s' % self.url)
            if exit_code != 0:
                sys.stderr.write('git failed\n')
                return exit_code
        elif self.type == 'hg':
            exit_code = os.system('hg clone %s' % self.url)
            if exit_code != 0:
                sys.stderr.write('hg failed\n')
                return exit_code
        elif self.type == 'distfile':
            # TODO: make this actually work
            os.system('wget %s' % self.url)
            os.system('unzip %s' % self.project)
        elif self.type == 'guess':
            # TODO: don't just assume it's on github
            exit_code = os.system('git clone git://github.com/%s/%s.git' %
                (self.user, self.project))
            if exit_code != 0:
                sys.stderr.write('git failed\n')
                return exit_code
        return 0

    def build(self):
        os.chdir(self.dir)
        if os.path.isfile('Makefile'):
            os.system('make')
        elif os.path.isfile('build.sh'):
            os.system('./build.sh')
        return 0  # TODO: only for now

### Subcommands

def dock_cmd(result, args):
    exit_code = 0
    sources = Source.parse_spec(args[0])
    for source in sources:
        exit_code = source.checkout()
        if exit_code != 0:
            break
        exit_code = source.build()
        if exit_code != 0:
            break
    if exit_code == 0:
        path_cmd(result, ['rebuild'])
    return exit_code


def path_cmd(result, args):
    if args[0] == 'rebuild':
        p = Path()
        p.remove_toolshelf_components()
        #sources = Source.load_docked()
        p.add_toolshelf_components()
        p.write(result)
        return 0
    else:
        sys.stderr.write("Unrecognized 'path' subcommand '%s'\n" % args[0])
        return 1


SUBCOMMANDS = {
    'dock': dock_cmd,
    'path': path_cmd,
}


if __name__ == '__main__':
    parser = OptionParser(__doc__)

    parser.add_option("-v", "--verbose", dest="verbose",
                      default=False, action="store_true",
                      help="report steps taken to standard output")

    (OPTIONS, args) = parser.parse_args()
    if len(args) == 0:
        print "Usage: " + __doc__
        sys.exit(2)

    exit_code = 0
    os.chdir(TOOLSHELF)
    result = LazyFile(RESULT_SH_FILENAME)
    subcommand = sys.argv[1]
    if subcommand in SUBCOMMANDS:
        exit_code = SUBCOMMANDS[subcommand](result, sys.argv[2:])
    else:
        sys.stderr.write("Unrecognized subcommand '%s'\n" % subcommand)
        print "Usage: " + __doc__
        sys.exit(2)
    result.close()
    sys.exit(exit_code)
