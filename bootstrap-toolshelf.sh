# Copyright (c)2012-2013 Chris Pressey, Cat's Eye Technologies
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
# prematurely stop (we can't do this by calling `exit`, because this script
# is being `source`d, and that would terminate the user's shell.)

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

    BASHRC=''
    if [ -e $HOME/.bashrc ]; then
        BASHRC="$HOME/.bashrc"
    fi
    if [ -e $HOME/.bash_profile ]; then
        BASHRC="$HOME/.bash_profile"
    fi

    if [ -z $BASHRC ]; then
        echo "***NOTE: You do not appear to have either a ~/.bashrc or"
        echo "a ~/.bash_profile."
        echo "toolshelf assumes you are using bash as your shell."
        echo "Please rectify this situation if you wish to use"
        echo "toolshelf, then re-source this script."
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
    echo -n "Directory? [${DEFAULT_TOOLSHELF}] "
    read -e TOOLSHELF
    if [ -z $TOOLSHELF ]; then
        TOOLSHELF=${DEFAULT_TOOLSHELF}
    fi
    echo
    echo "You selected: $TOOLSHELF"
    
    if [ -e $TOOLSHELF ]; then
        # TODO: actually loop here
        echo "Warning!  That directory already exists!"
        echo "If you would like to use it, type something here."
        echo "Otherwise press Ctrl-C to stop this script,"
        echo "re-source it, and make a different selection."
        echo
        echo -n "What'll it be? [continue] "
        read -e CONFIRM
    fi

    mkdir -p $TOOLSHELF
    echo "Proceeding to clone the toolshelf repo from github..."
    ORIGDIR=`pwd`
    cd $TOOLSHELF
    if [ "$DEBUG" = "DEBUG" ]; then
        cp -Rp $HOME/checkout/toolshelf .toolshelf
    else
        # TODO: check the return code of git here
        git clone git://github.com/catseye/toolshelf.git .toolshelf
    fi

    cd $ORIGDIR

    BASHRC1="source $TOOLSHELF/.toolshelf/init.sh $TOOLSHELF >/dev/null 2>&1 # added-by-bootstrap-toolshelf"

    echo "Now we'd like to add the following line to your $BASHRC file:"
    echo
    echo "  $BASHRC1"
    echo
    echo "Your current $BASHRC will be backed up first (to $BASHRC.orig),"
    echo "and any lines currently containing 'added-by-bootstrap-toolshelf'"
    echo "will be removed first."
    echo
    echo "If you don't want this script to touch your $BASHRC file, you"
    echo "may decline (but you'll have to add this line yourself.)"
    echo
    echo -n "Modify the file $BASHRC? [y/N] "
    read -e RESPONSE
    if [ -z $RESPONSE ]; then
        RESPONSE=N
    fi
    if [ $RESPONSE = 'y' -o $RESPONSE = 'Y' ]; then
        echo "Backing up $BASHRC and modifying it..."
        cp -p $BASHRC $BASHRC.orig
        grep -v 'added-by-bootstrap-toolshelf' <$BASHRC > $HOME/.new_bashrc
        echo >>$HOME/.new_bashrc "$BASHRC1"
        mv $HOME/.new_bashrc $BASHRC
        echo "Done."
        echo
        echo "For your convenience, we'll also apply these startup commands"
        echo "right now.  If you 'source'd this script like the instructions"
        echo "told you to, you'll be able to start using toolshelf right"
        echo "away.  If, instead, you started it using 'bash', you'll have"
        echo "to start a new bash shell to start using toolshelf."

        source $TOOLSHELF/.toolshelf/init.sh $TOOLSHELF
    else
        echo "That's totally fine; please make these changes yourself."
        echo "Then start a new bash shell to start using toolshelf."
    fi

    echo
    echo "Thanks for using the toolshelf bootstrap script!"

    return 0
}

bootstrap_toolshelf
