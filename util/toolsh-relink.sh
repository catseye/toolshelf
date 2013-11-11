#!/bin/sh

# An experimental re-implementation of 'toolshelf relink' in pure
# POSIX shell.  Requires that:
#     $TOOLSHELF be set.
#     the current directory is the directory of the docked source to be relinked.

# example:
#   thcd foo
#   sh $TOOLSHELF/.toolshelf/util/toolsh-relink.sh

# Obviously this script isn't very smart yet; that's why I said 'experimental.'
# In particular, it only cares about executables in the `bin` and `script`
# directories.

if [ -z $TOOLSHELF ]; then
   echo 'The environment variable TOOLSHELF must be set first.'
   exit 1
fi

# TODO: should go through the link farm and delete any links that point
# into here.  ha, that should be fun.

COMMAND="$1"

for DIR in bin script; do
    if [ -d $DIR ]; then
        cd $DIR
        for BIN in *; do
            if [ ! $BIN = '*' ]; then
                if [ -x $BIN ]; then
                    rm -f $TOOLSHELF/.bin/$BIN
                    FULLBIN=`pwd`"/$BIN"
                    echo ln -s $FULLBIN $TOOLSHELF/.bin/$BIN
                    ln -s $FULLBIN $TOOLSHELF/.bin/$BIN
                fi
            fi
        done
        cd ..
    fi
done
