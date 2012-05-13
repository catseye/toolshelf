#!/usr/bin/env python

# Invoked by `toolshelf.sh` (for which `toolshelf` is an alias) to do the
# heavy lifting involved in docking packages and placing their relevant
# directories on the search path.

# Still largely under construction.

import os
import sys


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
        self.components = value.split(':')


### Subcommands

def dock(result, args):
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
        path(result, ['rebuild'])
    return exit_code


def path(result, args):
    if args[0] == 'rebuild':
        result.write('echo Rebuild path')
        return 0
    else:
        sys.stderr.write("Unrecognized 'path' subcommand '%s'\n" % args[0])
        return 1


SUBCOMMANDS = {
    'dock': dock,
    'path': path,
}


if __name__ == '__main__':
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
