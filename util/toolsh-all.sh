#!/bin/sh

# An experimental re-implementation of 'toolshelf all' in pure
# POSIX shell.  Requires that $TOOLSHELF be set.

# example: sh util/toolsh-all.sh 'pwd && hg st'

# Obviously this script isn't very smart yet; that's why I said 'experimental.'

if [ -z $TOOLSHELF ]; then
   echo 'The environment variable TOOLSHELF must be set first.'
   exit 1
fi

COMMAND="$1"

cd $TOOLSHELF
for SITE in *; do
    if [ ! $SITE = '*' ]; then
        cd $SITE || exit 1
        for USER in *; do
            if [ ! $USER = '*' ]; then
                cd $USER || exit 1
                for REPO in *; do
                    if [ ! $REPO = '*' ]; then
                        cd $REPO || exit 1
                        eval $COMMAND
                        cd ..
                    fi
                done
                cd ..
            fi
        done
        cd ..
    fi
done
