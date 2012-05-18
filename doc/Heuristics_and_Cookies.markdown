Heuristics and Hints used by `toolshelf`
========================================

When you refer to a source, `toolshelf` tries to do a lot of clever guessing
about what source you mean, how to build it, and how to put its executables
on your search path.  It also allows you to supply explicit hints to help it
along in this process.

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

    toolshelf dock @/home/me/my-sources.catalog

will read a list of source specifications, one per line, from the given text
file (called a _catalog file_.)

♦ Several catalog files are supplied with `toolshelf` itself; you can use
the following specification as a shortcut for
`@$TOOLSHELF/.toolshelf/catalog/collection.catalog`:

    toolshelf dock @@collection

♦ To better accommodate tab-completion, `toolshelf` should also allow you
to pass the `@` or `@@` as a seperate argument on the command line, like:

    toolshelf dock @ ~/gezbo.catalog

### How does it know which directories to place on your path? ###

After a source tree has been docked and built (see below for building,)
`toolshelf` traverses the source tree, looking for executable files.  Every
time it finds one, it places the directory in which it found it into a working
set of directories.  It then adds that set of directories to your path.

(It adds them at the start of your `$PATH` variable, so that the executables
shadow (override) any executables with the same names that you might already
have installed.  It is easy to temporarily disable `toolshelf`'s modifications
to `$PATH` by running `toolshelf path disable` if you need to use the shadowed
executables.  You can reinstate the `toolshelf`-docked executables by running
`toolshelf path rebuild`.)

This approach occasionally results in useless executables on your
path, in the case where are files in the source tree which aren't really
executable, but have the executable bit (`+x`) set anyway, perhaps by
accident, or perhaps because they were taken off a filesystem which doesn't
support the idea of execute permissions.  Or, perhaps they are genuine
executables, but of limited day-to-day use (build scripts, test scripts,
demos, and the like.)

One specific instance of this problem arises when the files came from a `.zip`
archive, which doesn't store executable permission information on files.  In
this case, `toolshelf` traverses all of the files in the source tree just after
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

Hints
-----

`toolshelf` allows _hints_ to be supplied as part of a source
specification.  A hint specification is enclosed in curly brackets,
immediately following the source specification; for example,

    https://bitbucket.org/aristotle/nicomachean-ethics{o=bin:r=perl}

The hint specification consists of a colon-seperated list of hints.
Each hint consists of a hint name, an equals sign, and the hint value.

When a hint may be a list of values, the values are seperated by plus
signs in a single hint.

The choice of symbols here is intended to not clash with shell meta-
characters which may need escaping.  (We cannot use a comma instead of
a colon or a plus sign, or the shell will interpret the curly braces
as something to expand.)

Hint names are often one or two characters.  The meanings of these names
are as follows.

* ♦ `r` indicates a required executable.  When this is given, `toolshelf`
  first checks if you have the named executable on your path; if you do not,
  it will display an error message, and will not try to dock the source.
  Example: `r=perl`.

* ♦ `R` means rectify the execute permissions; after checking out the given
  source but before building it, traverse all of the files in the source
  tree, run `file` on each one, and set its executable permission based on
  whether `file` called it `executable` or not.  (This is the default for
  `.zip` archives.)  The value should be `y` to trigger this behavior.

* ♦ `d` indicates a dependency source tree.  When this is given, `toolshelf`
  first checks if you have the source named by the hint's value, a source
  specification, docked; if you do not, it will try to dock that source first.
  Example: `d=Scriptor/Pharen`.

* ♦ `x` indicates a directory subtree that you should not be added to the
  executable search path.  This could be useful if there are executables
  included in a source tree that you don't want put on your path, but
  `toolshelf` itself isn't clever enough to figure out that you don't want
  them.  Example: `x=tests/x86`.  Note that this rejects all directories that
  start with the text, so the example would prevent executables in all of the
  following directories from being put on the path: `tests/x86/passing`,
  `tests/x86/failing`, `tests/x8600`.

* ♦ `o` indicates that *only* these subdirectories should be added to the
  executable search path.  Example: `o=bin`.

* ♦ `E` indicates an environment variable to set to the name of the source
  tree directory.  (mnemonic: set.)  Many source distributions come with
  library files, example files, configuration files, or whatnot which are
  stored in the source tree, and this provides an easy method to find them.
  Example: `E=FOO`.  Then, after docking `foo`, you could say
  `foo $FOO/eg/eg.foo` to run an example `foo` program supplied in the
  distribution.

"Cookies"
---------

♦ `toolshelf` comes with a database of "cookies" which supplies extra
information (in the form of hints) about the idiosyncracies of particular,
known projects.

The use of the term "cookie" here is not like "HTTP cookie" or "magic cookie",
but more like how it was used in Windows 3.1 (and may, for all I know, still
be used in modern Windows.)  Such "cookies" informed the OS about how to deal
with particular hardware for which the generic handling was not sufficient.

This usage of the word is derived from the word "kooky" -- that is,
idiosyncratic and non-standard.

The "cookies" file for `toolshelf` consists of a list of source specifications
with hints.  When `toolshelf` is given a source specification which matches
one in the "cookies" file, it automatically applies those hints.  You can
probably override them with hints in the given source specification.

