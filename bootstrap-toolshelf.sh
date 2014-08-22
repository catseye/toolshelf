# Copyright (c)2012-2014 Chris Pressey, Cat's Eye Technologies
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

# bootstrap-toolshelf.sh:

# A script which sets up the toolshelf environment for you for the
# first time, intended to be `source`d.

# We structure this script as one big function (for now), so that we can
# prematurely stop (we can't do this by calling `exit`, because if this script
# is being `source`d, that would terminate the user's shell.)

# TODO: refactor this one function into smaller, more useful functions

DEBUG=$1

bootstrap_toolshelf() {
    echo
    echo "Welcome to the bootstrap script for toolshelf!"
    echo
    echo "Please report (in detail) any problems you encounter"
    echo "while running this script in the issue tracker:"
    echo
    echo "    https://github.com/catseye/toolshelf/issues"
    echo

    OK=1

    SHELL_PROFILE=''
    if [ -e $HOME/.profile ]; then
        SHELL_PROFILE="$HOME/.profile"
    fi
    if [ -e $HOME/.bashrc ]; then
        SHELL_PROFILE="$HOME/.bashrc"
    fi
    if [ -e $HOME/.bash_profile ]; then
        SHELL_PROFILE="$HOME/.bash_profile"
    fi

    if [ -z $SHELL_PROFILE ]; then
        echo "***NOTE: You do not appear to have a shell profile file"
        echo "(couldn't find ~/.bashrc, nor ~/.bash_profile, nor ~/.profile.)"
        echo
        echo "This script assumes you are using a POSIX-like"
        echo "(Bourne-shell based) shell, such as bash or dash,"
        echo "as your interactive shell.  Some feature of toolshelf"
        echo "assume this too, so this is the recommended configuration."
        echo
        echo "Please switch to such a shell if you wish to run this script."
        echo
        OK=0
    fi

    if [ -z `which python` ]; then
        echo "***NOTE: You do not appear to have Python installed."
        echo "Please install Python (version 2.6 or later) using "
        echo "your system's package manager (or by some other method),"
        echo "then re-source this script."
        echo
        OK=0
    fi

    # TODO: in the future, check for/allow hg too
    if [ -z `which git` ]; then
        echo "***NOTE: You do not appear to have git installed."
        echo "Please install git (version 1.7 or later) using "
        echo "your system's package manager (or by some other method),"
        echo "then re-source this script."
        echo
        OK=0
    fi

    if [ "$OK" = "0" ]; then
        return 1
    fi

    echo "You appear to have both 'python' and 'git' installed."
    echo "That's good.  We'll proceed."
    echo

    DEFAULT_TOOLSHELF="$HOME/toolshelf"
    echo "Please specify the directory in which toolshelf will"
    echo "store its source trees.  (If it does not yet exist,"
    echo "it will be created.)"
    echo
    echo "It is strongly recommended that this pathname not"
    echo "contain any spaces or other characters which"
    echo "normally require escaping for the shell; even if"
    echo "toolshelf handles all these cases correctly, there's"
    echo "a fair chance any random source that you dock won't."
    echo
    echo -n "Directory? [${DEFAULT_TOOLSHELF}] "
    read TOOLSHELF
    if [ -z $TOOLSHELF ]; then
        TOOLSHELF=${DEFAULT_TOOLSHELF}
    fi
    echo
    echo "You selected: $TOOLSHELF"

    if [ -e $TOOLSHELF ]; then
        # TODO: actually loop here
        echo "Warning!  That directory already exists!"
        echo
        echo "This script won't delete it, but may have problems"
        echo "using it, if there is already stuff inside it."
        echo
        echo "If you would like to use it, type something here."
        echo "Otherwise press Ctrl-C to stop this script,"
        echo "re-source it, and make a different selection."
        echo
        echo -n "What'll it be? [continue] "
        read CONFIRM
    fi

    mkdir -p $TOOLSHELF
    # TODO: check if $TOOLSHELF/.toolshelf already exists
    # TODO: prompt for where to clone toolshelf from
    echo "Proceeding to clone the toolshelf repo from github..."
    ORIGDIR=`pwd`
    cd $TOOLSHELF
    if [ "$DEBUG" = "DEBUG" ]; then
        cp -Rp $HOME/checkout/toolshelf .toolshelf
    else
        # TODO: check the return code of git here
        git clone https://github.com/catseye/toolshelf .toolshelf
    fi

    cd $ORIGDIR

    LINE1="export TOOLSHELF=$TOOLSHELF && . "'$'"TOOLSHELF/.toolshelf/init.sh # added-by-bootstrap-toolshelf"

    echo "Now we'd like to add the following line to your ${SHELL_PROFILE} file:"
    echo
    echo "  $LINE1"
    echo
    echo "Your current ${SHELL_PROFILE} will be backed up first"
    echo "(to ${SHELL_PROFILE}.orig),"
    echo "and any lines currently containing 'added-by-bootstrap-toolshelf'"
    echo "will be removed first."
    echo
    echo "If you don't want this script to touch your ${SHELL_PROFILE} file, you"
    echo "may decline (but you'll have to add this line yourself.)"
    echo
    echo -n "Modify the file ${SHELL_PROFILE}? [y/N] "
    read RESPONSE
    if [ -z $RESPONSE ]; then
        RESPONSE=N
    fi
    if [ $RESPONSE = 'y' -o $RESPONSE = 'Y' ]; then
        echo "Backing up ${SHELL_PROFILE} and modifying it..."
        cp -p ${SHELL_PROFILE} ${SHELL_PROFILE}.orig
        NEWFILE="$HOME/.tmp_new_profile_$$"
        grep -v 'added-by-bootstrap-toolshelf' <${SHELL_PROFILE} > ${NEWFILE}
        echo >>${NEWFILE} "$LINE1"
        mv ${NEWFILE} ${SHELL_PROFILE}
        echo "Done."
        echo
        echo "You may now start a new shell to begin using toolshelf."

        . $TOOLSHELF/.toolshelf/init.sh $TOOLSHELF
    else
        echo "That's totally fine; please make these changes yourself."
        echo "Then start a new bash shell to start using toolshelf."
    fi

    echo
    echo "Thanks for using the toolshelf bootstrap script!"

    return 0
}

bootstrap_toolshelf
