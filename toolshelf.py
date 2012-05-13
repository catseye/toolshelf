#!/usr/bin/env python

# Invoked by `toolshelf.sh` (for which `toolshelf` is an alias) to do the
# heavy lifting involved in docking packages and placing their relevant
# directories on the search path.

# Still largely under construction.

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
            subdir_name = os.path.join(TOOLSHELF, name)
            if not os.path.isdir(subdir_name):
                continue
            for candidate in ('bin', 'script', 'scripts'):
                bindir_name = os.path.join(subdir_name, candidate)
                if os.path.isdir(bindir_name):
                    print bindir_name
                    self.components.append(bindir_name)


### Subcommands

def dock_cmd(result, args):
    project_name = args[0]
    print 'Dock: ', project_name
    # TODO: look up project_name in database
    # if found, use details from there to know where to fetch it
    # and so forth.
    # if not found, assume it is a user/repo on github:
    url = 'git://github.com/%s.git' % project_name
    # TODO: perhaps use subprocess instead
    exit_code = os.system('git clone %s' % url)
    if exit_code == 0:
        path_cmd(result, ['rebuild'])
    return exit_code


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
    parser = OptionParser()
    parser.add_option("-v", "--verbose",
                      dest="verbose",
                      default=False,
                      action="store_true")

    (options, args) = parser.parse_args()
    if len(args) == 0:
        print "Usage: toolshelf <subcommand>"

    exit_code = 0
    os.chdir(TOOLSHELF)
    result = ResultShellFile()
    subcommand = sys.argv[1]
    if subcommand in SUBCOMMANDS:
        exit_code = SUBCOMMANDS[subcommand](result, sys.argv[2:])
    else:
        sys.stderr.write("Unrecognized subcommand '%s'\n" % subcommand)
        exit_code = 1
    result.close()
    sys.exit(exit_code)
