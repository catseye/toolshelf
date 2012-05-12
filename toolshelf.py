#!/usr/bin/env python

# Invoked by `toolshelf.py` (for which `toolshelf` is an alias) to do the
# heavy lifting involved in docking packages and placing their relevant
# directories on the search path.

# Woefully incomplete; just a stub for now.

import sys

if __name__ == '__main__':
    if sys.argv[1] == 'dock':
        print 'echo Dock: ' + ','.join(sys.argv[2:])
    elif sys.argv[1] == 'path':
        if sys.argv[2] == 'rebuild':
            print 'echo Rebuild path'
        else
            print 'echo Unrecognized path command'
    else
        print 'echo Unrecognized command'
