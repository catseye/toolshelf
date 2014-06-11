# sourced (using `.`) by your `.profile` (or `.bashrc` or whatever) to
# initialize the `toolshelf` environment in your shell session.  Also
# sourced by the bootstrap script.

# Non-`bash` shells can't necessarily receive arguments after the name of
# the file being sourced, so we insist the TOOLSHELF env var is
# set before this runs, and use that.  TOOLSHELF is expected to contain
# the fully-qualified path to the toolshelf directory (often, e.g.,
# `/home/user/toolshelf`.)

if [ -z $TOOLSHELF ]; then
  echo "error: TOOLSHELF env var must be set before sourcing init.sh"
elif [ ! -d $TOOLSHELF ]; then
  echo "error: TOOLSHELF does not refer to a valid directory"
else
  export PATH="$TOOLSHELF/.toolshelf/bin:$TOOLSHELF/.bin:$PATH"
  export LD_LIBRARY_PATH="$TOOLSHELF/.lib:$LD_LIBRARY_PATH"
  export LIBRARY_PATH="$TOOLSHELF/.lib:$LIBRARY_PATH"
  export C_INCLUDE_PATH="$TOOLSHELF/.include:$C_INCLUDE_PATH"
  export PYTHONPATH="$TOOLSHELF/.python:$PYTHONPATH"
  export PKG_CONFIG_PATH="$TOOLSHELF/.pkgconfig:$PKG_CONFIG_PATH"
  export LUA_PATH="$TOOLSHELF/.lua/?.lua;$TOOLSHELF/.lib/?.so;$LUA_PATH"

  # `toolshelf` itself can't change the shell's idea of the current working
  # directory, but a shell function can utilize `toolshelf` to do so.  Since
  # this is a *very* handy function of toolshelf, you may wish to make a short
  # alias for this, i.e. add a line like this to your shell profile or aliases
  # file:
  #    alias thcd=toolshelf_cd

  toolshelf_cd() {
      DIR=`$TOOLSHELF/.toolshelf/bin/toolshelf pwd $*`
      if [ ! -z $DIR ]; then
          cd $DIR
      fi
  }
fi
