#!/usr/bin/env python

# Invoked by `toolshelf.py` (for which `toolshelf` is an alias) to do the
# heavy lifting involved in docking packages and placing their relevant
# directories on the search path.

# Woefully incomplete; just a stub for now.

import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
RESULT_SH_FILENAME = os.path.join(SCRIPT_DIR, 'tmp-toolshelf-result.sh')


if __name__ == '__main__':
    if sys.argv[1] == 'dock':
        print 'Dock: ', ','.join(sys.argv[2:])
    elif sys.argv[1] == 'path':
        if sys.argv[2] == 'rebuild':
            result = open(RESULT_SH_FILENAME, 'w')
            result.write('echo Rebuild path')
            result.close()
        else
            print 'Unrecognized path command'
            sys.exit(1)
    else
        print 'Unrecognized command'
        sys.exit(1)
