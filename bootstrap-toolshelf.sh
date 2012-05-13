# be careful not to call `exit` here -- this script is being `source`d.
# TODO: rewrite as a bash function (should alleviate this)

echo
echo "Welcome to the bootstrap script for toolshelf!"
echo
echo "Please report (in detail) any problems you encounter"
echo "while running this script in the issue tracker:"
echo
echo "    https://github.com/catseye/toolshelf/issues"
echo

OK='1'

if [ ! -e $HOME/.bashrc ]; then
    echo "***NOTE: You do not appear to have a ~/.bashrc file."
    echo "toolshelf assuming you are using bash as your shell."
    echo "Please rectify this situation if you wish to use"
    echo "toolshelf, then re-source this script."
    echo
    OK='0'
fi

if [ -z `which python` ]; then
    echo "***NOTE: You do not appear to have Python installed."
    echo "Please install Python (version 2.6 or later) using "
    echo "your system's package manager (or by some other method),"
    echo "then re-source this script."
    echo
    OK='0'
fi

# TODO: in the future, check for/allow hg too
if [ -z `which git` ]; then
    echo "***NOTE: You do not appear to have git installed."
    echo "Please install git (version 1.7 or later) using "
    echo "your system's package manager (or by some other method),"
    echo "then re-source this script."
    echo
    OK='0'
fi

# TODO: check for existence of $HOME/.bashrc here too

if [ $OK = '1' ]; then
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
    # TODO: check the return code of git here
    git clone git://github.com/catseye/toolshelf.git
    cd $ORIGDIR

    BASHRC0="##################### added-by-bootstrap-toolshelf #####################"
    BASHRC1="if [ -f $TOOLSHELF/toolshelf/toolshelf.sh ]; then # added-by-bootstrap-toolshelf"
    BASHRC2="  export TOOLSHELF=\"$TOOLSHELF\" # added-by-bootstrap-toolshelf"
    BASHRC3="  alias toolshelf=\"source \$TOOLSHELF/toolshelf/toolshelf.sh\" # added-by-bootstrap-toolshelf"
    BASHRC4="  source \$TOOLSHELF/toolshelf/toolshelf.sh path rebuild # added-by-bootstrap-toolshelf"
    BASHRC5="fi # added-by-bootstrap-toolshelf"
    BASHRC6="##################### added-by-bootstrap-toolshelf #####################"

    echo "Now we'd like to add the following lines to your .bashrc file:"
    echo
    echo "  $BASHRC0"
    echo "  $BASHRC1"
    echo "  $BASHRC2"
    echo "  $BASHRC3"
    echo "  $BASHRC4"
    echo "  $BASHRC5"
    echo "  $BASHRC6"
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
        echo "Backing up .bashrc and modifying it..."
        cp -p $HOME/.bashrc $HOME/.bashrc.orig
        grep -v 'added-by-bootstrap-toolshelf' <$HOME/.bashrc > $HOME/.new_bashrc
        echo >>$HOME/.new_bashrc "$BASHRC0"
        echo >>$HOME/.new_bashrc "$BASHRC1"
        echo >>$HOME/.new_bashrc "$BASHRC2"
        echo >>$HOME/.new_bashrc "$BASHRC3"
        echo >>$HOME/.new_bashrc "$BASHRC4"
        echo >>$HOME/.new_bashrc "$BASHRC5"
        echo >>$HOME/.new_bashrc "$BASHRC6"
        mv $HOME/.new_bashrc $HOME/.bashrc
        echo "Done."
        echo
        echo "For your convenience, we'll also apply these startup commands"
        echo "right now.  If you 'source'd this script like the instructions"
        echo "told you to, you'll be able to start using toolshelf right"
        echo "away.  If, instead, you started it using 'bash', you'll have"
        echo "to start a new bash shell to start using toolshelf."
        echo

        export TOOLSHELF
        alias toolshelf="source $TOOLSHELF/toolshelf/toolshelf.sh"
        source $TOOLSHELF/toolshelf/toolshelf.sh path rebuild
    else
        echo "That's totally fine; please make these changes yourself."
        echo "Then start a new bash shell to start using toolshelf."
    fi
fi

echo
echo "Thanks for using the toolshelf bootstrap script!"
