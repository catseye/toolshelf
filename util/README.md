This directory contains some miscellaneous scripts.

`devstrap.sh` bootstraps the toolshelf in use to be docked under itself.

`toolsh-all.sh`, `toolsh-dock-distfile.sh`, and `toolsh-relink.sh` were
attempts to re-implement some core toolshelf functionality directly in
the Bourne shell.

This is a good idea.  We should plan to rewrite large chunks as standalone
scripts in Bourne shell + Lua.  (Lua is pre-installed on NetBSD.  Even on
systems where it is not pre-installed, it takes super much less time to
build from source than Python does.)

*   toolsh-pwd: parse specs and echo what directories they resolve to.
*   toolsh-build: build logic.
*   toolsh-rectperms: rectify_permissions logic.
*   toolsh-tether: tether logic.
*   toolsh-relink: relink logic.

Then the driver can do something like:

    CMD=$1
    SPECS=$*  # shift...
    if [ x"$CMD" = "x" ]; then
        usage()
    fi

    echo '' > $LOGFILE
    DIRS=`toolsh-pwd $SPECS`

    if [ $CMD = build ]; then
        for DIR in $DIRS; do
            cd $DIR
            toolsh-build >> $LOGFILE
        done
    elsif ...
    else
        usage()
    fi

    cat $LOGFILE

One complication is accessing cookies and hints and things.  `toolsh-gethint`,
written in Lua, I imagine, something like that.

