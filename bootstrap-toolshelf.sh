# be careful not to call `exit` here -- this script is being `source`d.

echo
echo "Welcome to the bootstrap script for toolshelf!"
echo
echo "Please report (in detail) any problems you encounter"
echo "while running this script in the issue tracker:"
echo
echo "    https://github.com/catseye/toolshelf/issues"
echo

OK='1'

if [ -z `which python` ]; then
    echo "***NOTE: You do not appear to have Python installed."
    echo "Please install Python (version 2.6 or later) using "
    echo "your system's package manager (or by some other method),"
    echo "then re-source this script."
    echo
    OK='0'
fi

# in the future, check for/allow hg too
if [ -z `which git` ]; then
    echo "***NOTE: You do not appear to have git installed."
    echo "Please install git (version 1.7 or later) using "
    echo "your system's package manager (or by some other method),"
    echo "then re-source this script."
    echo
    OK='0'
fi

if [ $OK = '1' ]; then
    echo "You appear to have both 'python' and 'git' installed."
    echo "That's good.  We'll proceed."
    echo

    DEFAULT_TOOLSHELF="$HOME/checkout"
    echo "Please specify the directory in which toolshelf will"
    echo "store its source trees.  (If it does not yet exist,"
    echo "it will be created.)"
    echo -n "Directory? [${DEFAULT_TOOLSHELF}] "
    read -e TOOLSHELF
    if [ -z $TOOLSHELF ]; then
        TOOLSHELF=${DEFAULT_TOOLSHELF}
    fi
    echo
    echo "You selected: $TOOLSHELF"
    # check if it already exists here
    mkdir -p $TOOLSHELF
    echo "Proceeding to clone the toolshelf repo from github..."
    ORIGDIR=`pwd`
    cd $TOOLSHELF
    git clone git://github.com/catseye/toolshelf.git
    cd $ORIGDIR

    # make changes to .bashrc here
    BASHRCADD=<<"EOV"
export TOOLSHELF="$TOOLSHELF" # added-by-bootstrap-toolshelf
alias toolshelf="source \$TOOLSHELF/toolshelf/toolshelf.sh # added-by-bootstrap-toolshelf
zero rebuild path # added-by-bootstrap-toolshelf
EOV

    echo "Now we'd like to add the following lines to your .bashrc file:"
    echo
    echo $BASHRCADD
    echo
    echo "Your current .bashrc will be backed up first (to .bashrc.orig),"
    echo "and any lines currently containing 'added-by-bootstrap-toolshelf'"
    echo "will be removed first."
    echo
    echo "If you don't want this script to touch your .bashrc file, you"
    echo "may decline (but you'll have to add these lines yourself.)"
    echo
    echo -n "Modify the file $HOME/.bashrc? [y/N] "
    read -e RESPONSE
    if [ -z $RESPONSE ]; then
        RESPONSE=N
    fi
    if [ $RESPONSE = 'y' -o $RESPONSE = 'Y' ]; then
        echo >>$HOME/.bashrc "$BASHRCADD"
    fi
fi
