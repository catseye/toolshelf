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
import sys
from optparse import OptionParser


SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
# TODO: maybe this should not default to the .. of the script dir if env var isn't there?
TOOLSHELF = os.environ.get('TOOLSHELF', os.path.join(SCRIPT_DIR, '..'))
RESULT_SH_FILENAME = os.path.join(SCRIPT_DIR, 'tmp-toolshelf-result.sh')


class ResultShellFile(object):
    def __init__(self, filename=RESULT_SH_FILENAME):
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


### Subcommands

def dock_cmd(result, args):
    project_name = args[0]
    (user_name, repo_name) = project_name.split('/')
    # TODO: look up project_name in database
    # if found, use details from there to know where to fetch it
    # and so forth.
    # if not found, assume it is a user/repo on github:
    url = 'git://github.com/%s.git' % project_name
    userdir_name = os.path.join(TOOLSHELF, user_name)
    if not os.path.isdir(userdir_name):
        os.mkdir(userdir_name)
    os.chdir(userdir_name)
    # TODO: perhaps use subprocess instead
    exit_code = os.system('git clone %s' % url)
    if exit_code != 0:
        sys.stderr.write('git failed\n')
        return exit_code
    os.chdir(os.path.join(userdir_name, repo_name))
    if os.path.isfile('Makefile'):
        os.system('make')
    elif os.path.isfile('build.sh'):
        os.system('./build.sh')
    path_cmd(result, ['rebuild'])
    return 0


def path_cmd(result, args):
    if args[0] == 'rebuild':
        p = Path()
        p.remove_toolshelf_components()
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

    (options, args) = parser.parse_args()
    if len(args) == 0:
        print "Usage: " + __doc__
        sys.exit(2)

    exit_code = 0
    os.chdir(TOOLSHELF)
    result = ResultShellFile()
    subcommand = sys.argv[1]
    if subcommand in SUBCOMMANDS:
        exit_code = SUBCOMMANDS[subcommand](result, sys.argv[2:])
    else:
        sys.stderr.write("Unrecognized subcommand '%s'\n" % subcommand)
        print "Usage: " + __doc__
        sys.exit(2)
    result.close()
    sys.exit(exit_code)
