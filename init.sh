# `source`d by your `.bashrc` to initialize the `toolshelf` environment in
# your shell session.  Also `source`d by the bootstrap script.  The name of
# the `toolshelf` directory is expected to be passed as the first argument.

export TOOLSHELF=$1
alias toolshelf="source $TOOLSHELF/.toolshelf/toolshelf.sh"
source $TOOLSHELF/.toolshelf/toolshelf.sh path rebuild