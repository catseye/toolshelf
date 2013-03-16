toolshelf
=========

**Version 0.0 -- subject to change radically**

`toolshelf` is a "package manager" which doesn't actually install any files.
Instead, it stores the source trees of sundry packages in a single directory,
and manages your search paths to include the relevant subdirectories of those
trees.  The source trees are typically the working directories of local `git`
or Mercurial clones, or they can be source distributions from downloaded
tarballs (which includes `.zip` archives).

`toolshelf` requires that you use `bash` as your shell.  It also requires
Python 2.7 to run the workhorse script.

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

    toolshelf dock gh:nelhage/reptyr

When that completes, you can run `reptyr` by simply typing

    reptyr

Convenient!  And if you ever want to get rid of `reptyr` from your system,
simply run

    rm -rf $TOOLSHELF/nelhage/reptyr

And, if you want to get rid of (almost) all trace of `toolshelf` and all of
the packages you've docked using it, simply

    rm -rf $TOOLSHELF

(For removal to be completely complete, you'd also want to remove the commands
that `bootstrap-toolshelf.sh` added to your `.bashrc`.  But if your `$TOOLSHELF`
directory doesn't exist, they won't run anyway.)

Status
------

While `toolshelf` works (try it out!), it is still a work in progress, so its
usage may be somewhat chaotic for now -- you may have to wipe out your
`$TOOLSHELF` directory, if a disruptive change is made in how source trees and
their metadata are organized.

`toolshelf` has been used successfully on Ubuntu 12.04 LTS and cygwin.  There
is no reason it would not also work on *BSD systems.  It will probably work on
Mac OS X; if you have a Mac, please try it and let me know.

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

* The array of possible build tools that are used by small, experimental
  software distributions is huge -- too large for `toolshelf`'s heuristics
  to ever realistically encompass.  It handles the most common ones
  (`autoconf`, `make`, and the like.)

* Small, experimental software distributions don't always include an automated
  build procedure, just instructions for a human, and `toolshelf` obviously
  can't follow those.

* Taking the previous two points together, you can't expect `toolshelf` to
  "just work" in any case that's not well-trodden.  (On the other hand, if
  you were going to install from source without `toolshelf`, you'd have to
  fiddle with your build environment anyway, so it's no worse than that.)

* Most operating systems impose a fixed limit on the size of an environment
  variable, and the search path is stored in an environment variable.  Thus
  you can hit a limit if you dock a large number of sources and/or sources
  which have a large number of executable directories.  This will possibly
  be addressed in a future version by switching to having a single "link
  farm" directory on the search path (cf. `pkgsrc`.)

* It does essentially no dependency tracking.  Upgrade one of your docked
  sources, and anything else you have that might rely on it might break.

* There are also lots of specific things it doesn't do yet, but since it
  might be possible to add those features, I won't list them here.

Heuristics
----------

This section describes how `toolshelf` goes about figuring out where it should
grab a source from, how it should build it, and what it should put on your
search paths; and how you can influence it when it's not clever enough to
figure these things out by itself.

When you refer to a source, `toolshelf` tries to do a lot of clever guessing
about what source you mean, how to build it, and how to put its executables
on your search path.  It also allows you to supply explicit hints to help it
along in this process.

Sections marked ♦ are not yet implemented.

### How does it know which source you mean? ###

#### When docking sources ####

When docking a source, the source must by explicitly specified, although
there are shortcuts you can use.  Unsurprisingly,

    toolshelf dock git://github.com/alincoln/Gettysburg-Address.git

will clone a `git` repo from github to use as the source.  Similarly,

    toolshelf dock https://bitbucket.org/plato/the-republic

will clone a Mercurial repo from Bitbucket.  And you can dock a vanilla,
non-version-controlled tarball by saying

    toolshelf dock http://example.com/distfiles/foo-1.0.tar.gz

(It will download the tarball to `$TOOLSHELF/.distfiles/foo-1.0.tar.gz`
and cache it there, extract it to a temporary directory, and place the
source tree in `$TOOLSHELF/example.com/distfile/foo-1.0`.  This will work
regardless of whether the tarball contains a single directory called
`foo-1.0`, as is standard, or if it is a "tarbomb" where all the files are
contained in the root of the tar archive.  Which is frowned upon.)

`toolshelf` understands a few shortcuts for Github and Bitbucket:

    toolshelf dock gh:alincoln/Gettysburg-Address
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

#### When referring to an already-docked source ####

When referring to a source which is already docked, `toolshelf` allows
you to give just the source's base name, omitting the site name and the
user name.  For example, to build the first source we docked above, you
can say

    toolshelf build Gettysburg-Address

If there is an ambiguity, one such source will be picked non-deterministically
(TODO: perhaps this should be an error?)  In this case, you must add both the
host name and the username to resolve the ambiguity:

    toolshelf build github.com/alincoln/Gettysburg-Address

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

If there is a script called `build.sh` or ♦ `make.sh`, it will run that.
Otherwise...

If there's an `autogen.sh` ♦ but no `configure`, it runs that first, to
create `configure`.

♦ If there's no `autogen.sh`, but there is a `configure.in`, it runs
`autconf` to create `configure`.

If there's a `configure`, it runs that, to create a `Makefile`.

If there's a `Makefile`, it runs `make`.

♦ If there's a `build.xml`, it runs `ant` instead.

### "Cookies" ###

**THIS SECTION DOES NOT YET TOTALLY REFLECT HOW THINGS PRESENTLY WORK AND IS
SUBJECT TO CHANGE**

`toolshelf` comes with a (small) database of "cookies" which supplies extra
information (hints) about the idiosyncracies of particular, known projects.
As you discover idiosyncracies of new software you try to dock, you can add
new hints to this database (and open a pull request to push them upstream for
everyone to benefit from.)

The use of the term "cookie" here is not like "HTTP cookie" or "magic cookie",
but more like how it was used in Windows 3.1 (and may, for all I know, still
be used in modern Windows.)  Such cookies informed the OS about how to deal
with particular hardware for which the generic handling was not sufficient.
This usage of the word is apparently derived from the word "kooky" -- that is,
idiosyncratic and non-standard.

In some ways, `toolshelf`'s cookies file is like the `Makefile`s used in
FreeBSD's package system -- the information contained in it is similar.
However, it is just a single file, and is parsed directly instead of being a
`Makefile`.

The cookies file for `toolshelf` consists of a list of source specifications
with hints.  When `toolshelf` is given a source specification which matches
one in the cookies file, it automatically applies those hints.

Example of an entry in the cookies file:

    gh:user/project
      exclude_paths tests
      build_command ./configure --with-lighter-fluid --no-barbecue && make

It should be possible to have a local cookies files that supplements
`toolshelf`'s supplied cookies file, at some point.

#### Hints ####

Hints are given, one per line, underneath a source specification in the
cookies file.  Each hint consists of the hint name, some whitespace, and
the hint value (the syntax of which is determined by the hint name.)

Hint names are verbose because they're more readable that way and you'll
probably just be copy-pasting them from other cookies in the cookies file.

It *may* be possible to give ad-hoc hints on the command line at some point,
but this is not a recommended practice, as you'll probably want to record
those hints for future use or for sharing.

The names of hints are as follows.

*   ♦ `requires_executables`
    
    Example: `requires_executables perl`
    
    A space-separated list of executables required to dock and run the source.
    When this is given, `toolshelf` first checks if you have the named
    executable on your executable search path; if you do not, it will display
    an error message, and will not try to dock the source.
    
*   ♦ `rectify_permissions`
    
    Example: `rectify_permissions yes`

    means rectify the execute permissions; after checking out the given
    source but before building it, traverse all of the files in the source
    tree, run `file` on each one, and set its executable permission based on
    whether `file` called it `executable` or not.  (This is the default for
    `.zip` archives.)
    
*   ♦ `prerequisites`
    
    Example: `prerequisites gh:Scriptor/Pharen`
    
    A space-separated list of  source specifications.  When this is given,
    `toolshelf` first checks if you have each of the sources given in the
    hint value, docked; if you do not, it will try to dock the source first.
    
*   `exclude_paths`
    
    A space-separated list of directory names that should not be added to the
    executable search path.  This could be useful if there are executables
    included in a source tree that you don't want put on your path, but
    `toolshelf` itself isn't clever enough to figure out that you don't want
    them.  Example: `x=tests/x86`.  Note that this rejects all directories that
    start with the text, so the example would prevent executables in all of the
    following directories from being put on the path: `tests/x86/passing`,
    `tests/x86/failing`, `tests/x8600`.
    
*   `only_paths`
    
    Example: `only_paths bin`
    
    A space-separated list of directory names.  If this hint is given, any
    `exclude_paths` hint is ignores, and *only* these subdirectories will be
    added to the executable search path.  Unlike `exclude_paths`, these
    directories are specific; i.e. if `bin/subdir` contains executables, but
    `only_paths bin` is given, `bin/subdir` will not be added to the search
    path.
    
*   ♦ `build_command`
    
    Example: `build_command ./configure --no-cheese && make`
    
    specifies a command to run to build the source.  Passes the entire hint
    value to the shell for execution.  The command will be run with the root
    of the source tree as the working directory. 

Theory of Operation
-------------------

This section describes how it all works -- specifically, how typing
`toolshelf` can seemingly magically alter your search paths.

### `bootstrap-toolshelf.sh` ###

The bootstrap script does a few things:

- It checks that you have `git` and `python` installed.  If you don't, it asks
  you to install them, and stops.
- It asks you where you want to store source trees for the packages you dock
  using toolshelf; it calls this `$TOOLSHELF`.  The default is
  `$HOME/toolshelf`.
- It then clones the `toolshelf` git repo into `$TOOLSHELF/toolshelf`.
- It then asks permission to modify your `.bashrc` (if you decline, you are
  asked to make these changes manually.)  It adds a line that `source`s
  `init.sh` (see below.)
- Finally, it `source`s `init.sh` itself, so that `toolshelf` is available
  immediately after bootstrapping (you don't need to start a new shell.)

### `init.sh` ###

The script `init.sh` initializes `toolshelf` for use; it is typically
`source`d from within `.bashrc`.  This is what it does:

-   Takes a single command-line argument, which is the `toolshelf` directory,
    and exports it as the `TOOLSHELF` environment variable
-   Defines a `bash` function called `toolshelf`, which does the following:
    -   It runs `$TOOLSHELF/toolshelf/toolshelf.py`, with the arguments that
        were passed to the `toolshelf` function, expecting it to output a
        temporary file -- then it `source`s that temporary file and deletes
        it.
-   runs `toolshelf path rebuild`

The `toolshelf` function and the `toolshelf.py` script, taken together,
perform something which we could call the "shell-then-source trick".  In
effect, it makes it possible for a "command" (really a `bash` function) to
affect the environment of the user's current interactive shell -- something
an ordinarily invoked command cannot do.  This is what lets `toolshelf`
immediately alter your search paths.

In a shell which unlike `bash` does not support functions, this could also
be done (soemwhat more crudely) with an alias.

### `toolshelf.py` ###

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

* `toolshelf dock `[`gh:nelhage/reptyr`][]

  `reptyr` is a Linux utility, written in C, for attaching an already-running
  process to a GNU `screen` session.  It lives in a github repo.  Because it's
  Linux-specific, its build process is simple and `toolshelf` has no problem
  figuring out how to build it and put it on the executable search path.

* `toolshelf dock `[`bb:catseye/yucca`][]

  `yucca` is a Python program for performing static analysis on 8-bit BASIC
  programs.  Because it's written in Python, it doesn't need building, and
  because it has no dependencies on external Python libraries, it doesn't need
  anything besides Python to run.

  `yucca` is hosted on Bitbucket, with a git mirror on github; `toolshelf` can
  obtain the source from either site, using Mercurial or git respectively.
  (One day it will do this automatically; for now, the full URL of the remote
  repo must be specified.)

* `toolshelf dock `[`gh:kulp/tenyr`][]

  `tenyr` is an aspiring 32-bit toy computational environment.  `toolshelf`
  has no problem building it, finding the built executables, and putting them
  on your path.

  In `toolshelf`'s cookies database, this source has the hint
  `exclude_paths bench ui hw scripts` associated with it; it says to decline
  putting any paths from this project which begin with `bench`, `ui`, `hw`,
  or `scripts` onto the search path.  This prevents several scripts with
  rather generic names, and which you would typically not use frequently, from
  appearing on the search path.  These scripts can still be run by giving the
  full path to them, of course.

* `toolshelf dock `[`http://ftp.gnu.org/gnu/bison/bison-2.5.tar.gz`][]

  Is your system `bison` version 2.4, but you need version 2.5 installed
  temporarily in order to build `kulp/tenyr`?  No problem; just put it on
  your `toolshelf` with the above command.  After it's docked, you can issue
  the commands `toolshelf path disable ftp.gnu.org/bison-2.5` and
  `toolshelf path rebuild ftp.gnu.org/bison-2.5` to remove or reinstate
  it from your search path, respectively.  Similar to `tenyr`, this source has
  the hint `exclude_paths tests etc examples build-aux` associated with it.

[`gh:nelhage/reptyr`]: https://github.com/nelhage/reptyr
[`bb:catseye/yucca`]: https://bitbucket.org/catseye/yucca
[`gh:kulp/tenyr`]: https://github.com/kulp/tenyr
[`http://ftp.gnu.org/gnu/bison/bison-2.5.tar.gz`]: http://www.gnu.org/software/bison/bison.html

Related Work
------------

* [checkoutmanager][]

* [Gobolinux][]

* [pathify][]

* [sources][]

* [spackle][]

* `zero-install`/`0launch`

[checkoutmanager]: https://bitbucket.org/reinout/checkoutmanager
[Gobolinux]: http://gobolinux.org/
[pathify]: https://github.com/kristi/pathify
[sources]: https://github.com/trentm/sources
[spackle]: https://github.com/kristi/spackle
