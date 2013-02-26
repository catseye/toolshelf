toolshelf
=========

**CAUTION, UNDER RECONSTRUCTION. USE AT OWN RISK.**

`toolshelf` is a "package manager" which doesn't actually install any files.
Instead, it stores the source trees of sundry packages in a single directory,
and manages your search paths to include the relevant subdirectories of those
trees.  The source trees are typically the working directories of local `git`
or Mercurial clones, or they can be source distributions from tarballs.

`toolshelf` requires that you use `bash` as your shell.  It also requires
Python to run the workhorse script.

`toolshelf` is placed under an MIT-style license.

Quick Start
-----------

1. Download [`bootstrap-toolshelf.sh`][].
2. Start a `bash` shell (if you haven't already) and change to the directory
   where you downloaded `bootstrap-toolshelf.sh`.
3. Run `source bootstrap-toolshelf.sh`.
4. Follow the instructions given to you by the script.

[`bootstrap-toolshelf.sh`]: https://raw.github.com/catseye/toolshelf/master/bootstrap-toolshelf.sh

Now, you can dock (this is the word `toolshelf` uses instead of "install")
any source that `toolshelf` can handle, simply by typing, for example,

    toolshelf dock nelhage/reptyr

When that completes, you can run `reptyr` by simply typing

    reptyr

Convenient!  And if you ever want to get rid of `reptyr` from your system, simply

    rm -rf $TOOLSHELF/nelhage/reptyr

And, if you want to get rid of (almost) all trace of `toolshelf` and all of
the packages you've docked using it, simply

    rm -rf $TOOLSHELF

(For removal to be completely complete, you'd also want to remove the commands
that `bootstrap-toolshelf.sh` added to your `.bashrc`.  But if your `$TOOLSHELF`
directory doesn't exist, they won't run anyway.)

Status
------

While `toolshelf` works (try it out!), it is still a work in progress, so usage
of it may be somewhat chaotic for now -- you may have to wipe out your
`$TOOLSHELF` directory, if a disruptive change is made in how source trees and
their metadata are organized.

`toolshelf` has been used successfully on Ubuntu 11.10 and cygwin.  It should
probably work on Mac OS X; if you have a Mac, please try it and let me know.

Why `toolshelf`?
----------------

This section describes why I wrote `toolshelf`, and what it's aptitude's good
at and not so good at.

I've always been a little disturbed by the practice of running something like
`sudo make install` and having it write files into a whole bunch of places
in your filesystem -- `/usr/bin` (or `/usr/local/bin` or `/usr/pkg/` depending
on your OS), `/usr/lib`, and so forth, without even recording what it
installed where.  If you ever want to get rid of what you installed, you're
relying on the distribution's uninstall procedure (if any) to be correct.  If
you install a lot of experimental software from source, you're heading towards
having a system with a bunch of junk in it that you will, in practice, never
clean up.

So, I got into the habit of installing everything in my home directory.  At
least then, I could blow away my home directory if I wanted to clean
everything up.  For distributions that include a `configure` script or
similar, this is usually as easy as specifying `--prefix=$HOME` as an argument
to it -- then making sure `$HOME/bin` is on your path, and perhaps `$HOME/lib`
is added to your `LD_LIBRARY_PATH`.

But even then, things in `$HOME/bin` can conflict with my personal scripts,
and after enough installs, my home directory is basically impossible to clean
up too.  And, although I could, I don't really want to blow it away (I mean...
it *is* my home directory, after all.)

So I decided I should write `toolshelf`.

### Advantages ###

* When it works, it's pretty slick.  Issue one command, and when it finishes,
  you can immediately issue new commands from the software you "installed".

* It doesn't clutter up the system directories, or your home directory.  You
  can remove a source tree (or the whole kit and kaboodle) with a single
  `rm -rf`, and you know you got everything.

* It encourages hackability.  The sources are there -- if you have a problem,
  go edit them.  If they're in a repo, you can commit and branch and restore
  a previous version and whatever.  If you have push privleges for an upstream
  repo, you can send your changes off there.

### Limitations ###

* It doesn't always work, and can't always work for every piece of software
  out there.

* It's at its best for small, experimental software distributions -- the
  kind you might want to play with, but maybe not keep around forever.
  It's not designed for real meat-and-potatoes system software.  So, for
  example, if a package is written in Ruby, docking that package is not
  going to install Ruby for you if it's not already installed; the onus is on
  you to install Ruby if the package needs it.

* It does essentially no dependency tracking.  Upgrade one of your docked
  sources, and anything else you have that might rely on it might break.

* There are also lots of specific things it doesn't do yet, but since it
  might be possible to add those features, I won't list them here.

Heuristics
----------

This section describes how `toolshelf` goes about figuring out
where it should grab the source from, how it should build it, and what it
should put on your search paths; and how you can influence it when it's not
clever enough to figure these things out by itself.

When you refer to a source, `toolshelf` tries to do a lot of clever guessing
about what source you mean, how to build it, and how to put its executables
on your search path.  It also allows you to supply explicit hints to help it
along in this process.

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

♦ `toolshelf` understands a few shortcuts for Github and Bitbucket:

    toolshelf dock gh:alincoln/Gettysburg-Address.git
    toolshelf dock bb:plato/the-republic

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

### Hints ###

**THIS IS TOTALLY GOING TO BE REWRITTEN**

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

* `x` indicates a directory subtree that you should not be added to the
  executable search path.  This could be useful if there are executables
  included in a source tree that you don't want put on your path, but
  `toolshelf` itself isn't clever enough to figure out that you don't want
  them.  Example: `x=tests/x86`.  Note that this rejects all directories that
  start with the text, so the example would prevent executables in all of the
  following directories from being put on the path: `tests/x86/passing`,
  `tests/x86/failing`, `tests/x8600`.

* ♦ `o` indicates that *only* these subdirectories should be added to the
  executable search path.  Example: `o=bin`.

* ♦ `b` specifies a command to run to build the source.  Not sure if it will
  be passed to a shell for execution, or just split into words at the spaces.
  The command will be run with the root of the source tree as the working
  directory.  Note that if the command contains spaces, and the source spec
  is given on the command line, it will need to be quoted.
  Example: `b=tools/make-it`.

* ♦ `E` indicates an environment variable to set to the name of the source
  tree directory.  (mnemonic: set.)  Many source distributions come with
  library files, example files, configuration files, or whatnot which are
  stored in the source tree, and this provides an easy method to find them.
  Example: `E=FOO`.  Then, after docking `foo`, you could say
  `foo $FOO/eg/eg.foo` to run an example `foo` program supplied in the
  distribution.

### "Cookies" ###

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

Theory of Operation
-------------------

See [Theory of Operation][] for how it works -- specifically, how typing
`toolshelf` can seemingly magically alter your search paths.

`bootstrap-toolshelf.sh`
------------------------

The bootstrap script does a few things:

- It checks that you have `git` and `python` installed.  If you don't, it asks
  you to install them, and stops.
- It asks you where you want to store source trees for the packages you dock
  using toolshelf; it calls this `$TOOLSHELF`.  The default is
  `$HOME/toolshelf`.
- It then clones the `toolshelf` git repo into `$TOOLSHELF/toolshelf`.
- It then asks permission to modify your `.bashrc` (if you decline, you are
  asked to make these changes manually.)  It adds a command sequence to it
  that:
  * exports the `TOOLSHELF` environment variable
  * defines an alias called `toolshelf` which `source`s the script
    `$TOOLSHELF/toolshelf/toolshelf.sh`
  * runs `toolshelf path rebuild`
- Finally, it exports `TOOLSHELF` and defines the `toolshelf` alias and runs
  `toolshelf path rebuild` itself, so you can start using `toolshelf` as soon
  as the bootstrap script finishes, instead of having to start a new shell.

`toolshelf.sh`
--------------

The script `toolshelf.sh` does one thing, and does it well:

- It runs `$TOOLSHELF/toolshelf/toolshelf.py`, with the arguments that were
  passed to `toolshelf.sh`, expecting it to output a temporary file -- then
  it `source`s that temporary file and deletes it.

The `toolshelf` alias and the `toolshelf.sh` script, taken together, perform
something which we could call the "double-source trick".  In effect, it makes
it possible for a "command" (really an alias) to affect the environment of
the user's current interactive shell -- something an ordinarily invoked
command cannot do.  This is what lets `toolshelf` immediately alter your
search paths.

`toolshelf.py`
--------------

The Python script `toolshelf.py` is the workhorse:

- It checks its arguments for an appropriate subcommand.
- For the subcommand `dock`, it expects to find a source specifier.  It parses
  that specifier to determine where it should find that source.  It attempts
  to obtain that source (using `git clone` or whatever) and places the source
  tree under a subdirectory (organized by user name or domain name) under
  `$TOOLSHELF`.  It then decides if the obtained source needs building, and if
  so, builds it.  It then calls `toolshelf path rebuild` (internally) to
  rebuild the path.
- For the subcommand `path`, it checks for a further sub-subcommand.
  If the sub-subcommand is `rebuild`, it reads the `PATH` environment variable,
  removes all `$TOOLSHELF` entries from it, then traverses the source trees
  under `$TOOLSHELF` looking for executable files, and places the directories
  in which those executable files were found back into the `PATH`; then it
  outputs the command `export PATH={{path}}`.  (`toolshelf.sh` `sources` this
  to make the new path available to your shell immediately.)
- It checks for other arguments as needed.  Since it's trivial to remove a
  package that has been docked, there might not be a `undock` subcommand.

Case Studies
------------

This is just a sampling of sources I've tried with `toolshelf` so far, and
description of how well they work with the `toolshelf` model, and why.

* `toolshelf dock `[`nelhage/reptyr`][]

  `reptyr` is a Linux utility, written in C, for attaching an already-running
  process to a GNU `screen` session.  It lives in a github repo.  Because it's
  Linux-specific, its build process is simple and `toolshelf` has no problem
  figuring out how to build it and put it on the executable search path.

* `toolshelf dock `[`https://bitbucket.org/catseye/yucca`][]

  `yucca` is a Python program for performing static analysis on 8-bit BASIC
  programs.  Because it's written in Python, it doesn't need building, and
  because it has no dependencies on external Python libraries, it doesn't need
  anything besides Python to run.

  `yucca` is hosted on Bitbucket, with a git mirror on github; `toolshelf` can
  obtain the source from either site, using Mercurial or git respectively.
  (One day it will do this automatically; for now, the full URL of the remote
  repo must be specified.)

* `toolshelf dock `[`kulp/tenyr`][]`{x=scripts}`

  `tenyr` is an aspiring 32-bit toy computational environment.  `toolshelf`
  has no problem building it, finding the built executables, and putting them
  on your path.

  `{x=scripts}` is a hint specifier which says to decline putting any paths
  from this project on the search path if they start with `scripts`.  This
  prevents the scripts that ship with `tenyr` from being put on your path
  (because they have rather generic names, and are probably not things that
  you would use frequently.)

* `toolshelf dock `[`http://ftp.gnu.org/gnu/bison/bison-2.5.tar.gz`][]`{x=tests:x=etc:x=examples:x=build-aux}`

  Is your system `bison` version 2.4, but you need version 2.5 installed
  temporarily in order to build `kulp/tenyr`?  No problem; just put it on
  your `toolshelf` with the above command.  After it's docked, you can issue
  the commands `toolshelf path disable ftp.gnu.org/bison-2.5` and
  `toolshelf path rebuild ftp.gnu.org/bison-2.5` to remove or reinstate
  it from your search path, respectively.

[`nelhage/reptyr`]: https://github.com/nelhage/reptyr
[`https://bitbucket.org/catseye/yucca`] https://bitbucket.org/catseye/yucca
[`kulp/tenyr`]: https://github.com/kulp/tenyr
[`http://ftp.gnu.org/gnu/bison/bison-2.5.tar.gz`]: http://www.gnu.org/software/bison/bison.html

Related Work
------------

* `sources`

* `zero-install`/`0launch`

* `checkoutmanager`

