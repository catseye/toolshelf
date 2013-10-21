# `source`d by your `.bashrc` to initialize the `toolshelf` environment in
# your shell session.  Also `source`d by the bootstrap script.  The name of
# the `toolshelf` directory is expected to be passed as the first argument.

export TOOLSHELF=$1
export PATH="$TOOLSHELF/.toolshelf/bin:$TOOLSHELF/.bin:$PATH"

# `toolshelf` itself can't change the shell's idea of the current working directory,
# but a bash function can utilize `toolshelf` to do so.  Since this is a very handy
# function of toolshelf, you may wish to make a short alias for this, e.g. `thcd`.
function toolshelf_cd {
    DIR=`$TOOLSHELF/.toolshelf/bin/toolshelf pwd $*`
    if [ ! -z $DIR ]; then
        cd $DIR
    fi
}
