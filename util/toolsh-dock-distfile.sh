#!/bin/sh

# An experimental implementation of 'toolshelf dock' in pure POSIX shell.
# Requires that:
#     $TOOLSHELF be set.
#     the name of an already downloaded .tar.gz distfile 
#       be passed as the first argument.

# example:
#   sh $TOOLSHELF/.toolshelf/util/toolsh-dock-distfile.sh /cdrom/Python-2.7.6.tgz

# Obviously this script isn't very smart yet; that's why I said 'experimental.'

if [ -z $TOOLSHELF ]; then
   echo 'The environment variable TOOLSHELF must be set first.'
   exit 1
fi

DISTFILE="$1"



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
