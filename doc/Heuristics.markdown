Heuristics used by `toolshelf`
==============================

How does it know where to grab a source from?
---------------------------------------------

This is easiest to answer when the source is explicitly specified.  Unsurprisingly,

    toolshelf dock git://github.com/alincoln/gettysburg-address.git

will clone a `git` repo from github to use as the source.  Similarly,

    toolshelf dock https://bitbucket.org/plato/The-Republic

will clone a Mercurial repo from Bitbucket.  And you can even bring in a vanilla,
non-version-controlled tarball by saying

    toolshelf dock http://example.com/distfiles/monterey-jack-1.0.tar.gz

(It will place the source tree in a directory called `example.com/monterey-jack-1.0`
under `$TOOLSHELF`.)

The guesswork comes in when you just say

    toolshelf dock user/project

For now, it assumes that is a project on github.  But ideally, it should consult
preferences that you have configured, and try several servers in turn until it
finds one which matches the given user and project.

How does it know which directories to place on your path?
---------------------------------------------------------

After a source tree has been docked and built (see below for building,) `toolshelf`
traverses the source tree, looking for executable files.  Every time it finds one,
it places the directory in which it found it into a working set of directories.
It then adds that set of directories to your path.

This occasionally results in useless directories (and executables) on your path, in
the case where are files in the source tree which aren't really executable, but have
the executable bit (`+x`) set anyway, perhaps by accident, or perhaps because they
were taken off a filesystem which doesn't support the idea of execute permissions.

How does it know how to build the executables from the sources?
---------------------------------------------------------------

(Note: some of this isn't implemented yet.)

If there's a `Makefile`, it runs `make`.

If there's no `Makefile`, but there is a `configure`, it runs `configure`,
then runs `make`.

If there's no `configure` either, but there is a `configure.in`, it runs
`autconf`, then `configure`, then `make` (although I'll be surprised if I
ever see this succeed.)

If there's a `build.xml`, it runs `ant` instead.

If there's none of this, but there is a script called `build.sh` or
`make.sh`, it'll run that.
