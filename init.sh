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
  exit 1
fi

if [ ! -d $TOOLSHELF ]; then
  echo "error: TOOLSHELF does not refer to a valid directory"
  exit 1
fi

export PATH="$TOOLSHELF/.bin:$PATH"
export LD_LIBRARY_PATH="$TOOLSHELF/.lib:$LD_LIBRARY_PATH"
export LIBRARY_PATH="$TOOLSHELF/.lib:$LIBRARY_PATH"
export C_INCLUDE_PATH="$TOOLSHELF/.include:$C_INCLUDE_PATH"
export PYTHONPATH="$TOOLSHELF/.python:$PYTHONPATH"
export PKG_CONFIG_PATH="$TOOLSHELF/.pkgconfig:$PKG_CONFIG_PATH"
export LUA_PATH="$TOOLSHELF/.lua/?.lua;$TOOLSHELF/.lib/?.so;$LUA_PATH"

toolshelf() {
  if [ x$1 = xcd ]; then
    shift
    DIR=`$TOOLSHELF/.toolshelf/bin/toolshelf.py --unique resolve $*`
    if [ ! -z $DIR ]; then
      cd $DIR
    fi
  else
    $TOOLSHELF/.toolshelf/bin/toolshelf.py $*
  fi
}
