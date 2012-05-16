Heuristics and "Cookies" used by `toolshelf`
============================================

When you refer to a source, `toolshelf` tries to do a lot of clever
guessing about what source you mean, how to build it, and how to put
its executables on your search path.  It also allows you to give it
more explicit hints ("cookies") to help it along in this process.

Heuristics
----------

Sections marked ♦ are not yet implemented.

### How does it know where to grab a source from? ###

This is easiest to answer when the source is explicitly specified.
Unsurprisingly,

    toolshelf dock git://github.com/alincoln/Gettysburg-Address.git

will clone a `git` repo from github to use as the source.  Similarly,

    toolshelf dock https://bitbucket.org/plato/the-republic

will clone a Mercurial repo from Bitbucket.  And you can even bring in a
vanilla, non-version-controlled tarball by saying

    toolshelf dock http://example.com/distfiles/foo-1.0.tar.gz

(It will place the source tree in a directory called `example.com/foo-1.0`
under `$TOOLSHELF`.)

The guesswork comes in when you just say

    toolshelf dock user/project

For now, it assumes that is a project on github.  ♦ But ideally, it should
consult preferences that you have configured, and try several servers in turn
until it finds one which matches the given user and project.

This syntax is called a _source specification_.  There are a few other source
specifications you can use.  For example,

    toolshelf dock @/home/me/my-sources.txt

will read a list of source specifications, one per line, from the given text
file (called a _catalog file_.)

### How does it know which directories to place on your path? ###

After a source tree has been docked and built (see below for building,)
`toolshelf` traverses the source tree, looking for executable files.  Every
time it finds one, it places the directory in which it found it into a working
set of directories.  It then adds that set of directories to your path.

This occasionally results in useless directories (and executables) on your
path, in the case where are files in the source tree which aren't really
executable, but have the executable bit (`+x`) set anyway, perhaps by
accident, or perhaps because they were taken off a filesystem which doesn't
support the idea of execute permissions.

One specific instance of this is when the files came from a `.zip` archive,
which doesn't store executable permission information on files.  In this case,
`toolshelf` traverses all of the files in the source tree just after
extracting them from the archive, running `file` on each one, and setting its
executable permission based on whether `file` called it `executable` or not.

### How does it know how to build the executables from the sources? ###

If there's a `Makefile`, it runs `make`.

If there's no `Makefile`, but there is a `configure`, it runs `configure`,
then runs `make`.

♦ If there's no `configure` either, but there is a `configure.in`, it runs
`autconf`, then `configure`, then `make` (although I'll be surprised if I
ever see this succeed.)

♦ If there's a `build.xml`, it runs `ant` instead.

If there's none of this, but there is a script called `build.sh`, it'll run
that.  ♦ Or, if there's a `make.sh`, it'll run that.

"Cookies"
---------

(TODO: explain "cookies" here)

♦ `toolshelf` allows "cookies" to be specified as part of a source
specification.  The cookie specification is enclosed in curly brackets,
immediately following the source specification; for example,

    https://bitbucket.org/aristotle/nicomachean-ethics{-T:*perl}

The cookie specification consists of a colon-seperated list of cookies.
Each cookie begins with a particular character symbol.  The meanings of
these symbols are as follows.

* `-` indicates an option (mnemonic: like the command line.)  Each option
  has a different meaning, and may affect various aspects of how the source
  is docked.

  * `-T` means put the executables for this source at the top of the search
    path, where they will shadow all other executables of the same name
    (even executables in your system, like `/usr/bin/foo`.)

  * `-B` means put the executables for this source at the bottom of the search
    path, where they won't shadow anything.  (This is the default.)

  * `-R` means rectify the execute permissions; after checking out the given
    source but before building it, traverse all of the files in the source
    tree, run `file` on each one, and set its executable permission based on
    whether `file` called it `executable` or not.  (This is the default for
    `.zip` archives.)

  Some of these options *may* be allowable on the command line itself, in
  which case they would apply to all source specifications given.

* `*` indicates a prerequisite executable (mnemonic: *some assembly
  required.)  When this is given, `toolshelf` first checks if you have the
  named executable on your path (using `which`); if you do not, it will
  display an error message, and will not try to dock the source.
  Example: `*perl`.

* `!` indicates a prerequisite source tree (mnemonic: hey!  you need this
  first!)  When this is given, `toolshelf` first checks if you have the source
  named by the given specification docked; if you do not, it will try to dock
  that source first.  Example: `!Scriptor/Pharen`.  Because `?` is a shell
  metacharacter, it will need to be escaped if given on the command line, but
  the use of a `?` cookie on the command line is probably rare anyway (it
  makes more sense in a catalog file.)

* `%` indicates a directory subtree that you should not be added to the
  executable search path (mnemonic: the slash suggests a directory, and the
  two circles suggest zeros... the directory has been nullified.)  This could
  be useful if there are executables included in a source tree that you don't
  want put on your path, but `toolshelf` isn't otherwise clever enough to
  figure out that you don't want them.  Example: `%tests/x86`.  Note that
  this rejects all directories that start with the text, so the example
  would prevent executables in all of the following directories from being
  put on the path: `tests/x86/passing`, `tests/x86/failing`, `tests/x8600`.

* `=` indicates an environment variable to set to the name of the source
  tree directory.  (mnemonic: set.)  Many source distributions come with
  library files, example files, configuration files, or whatnot which are
  stored in the source tree, and this provides an easy method to find them.
  Example: `=FOO`.  Then, after docking `foo`, you could say
  `foo $FOO/eg/eg.foo` to run an example `foo` program supplied in the
  distribution.

Note that, because `*`, `!`, and `?` are shell metacharacters, they may need
to be escaped if given on the command line.  (`*` and `?` might not if there
are no files in the current directory that match the pattern they specify, but
`!` always will.  However, I've tried to select meanings for these cookies
which would likely be rarely used on the command line; they generally make
more sense in a catalog file.
