`toolshelf` — Theory of Operation
=================================

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

will clone a Mercurial repo from Bitbucket.  It does not know that

    toolshelf dock https://github.com/alincoln/Gettysburg-Address

is *not* a Mercurial repo, but in fact a git repo, so what it does in this
case is to try cloning it with Mercurial first, then if that fails, it tries
git.

And you can dock a vanilla, non-version-controlled tarball by saying

    toolshelf dock http://example.com/distfiles/foo-1.0.tar.gz

(It will download the tarball to `$TOOLSHELF/.distfiles/foo-1.0.tar.gz`
and cache it there, extract it to a temporary directory, and place the
source tree in `$TOOLSHELF/example.com/distfile/foo-1.0`.  This will work
regardless of whether the tarball contains a single directory called
`foo-1.0`, as is standard, or if it is a "tarbomb" where all the files are
contained in the root of the tar archive.  Which is frowned upon.)

`toolshelf` understands a few shortcuts for Github and Bitbucket:

    toolshelf dock gh:hhesse/Steppenwolf
    toolshelf dock bb:jswift/amodestproposal

This syntax is called a _source specification_.  There are a few other source
specifications you can use.  For example,

    toolshelf dock @/home/me/my-sources.catalog

will read a list of source specifications, one per line, from the given text
file (called a _catalog file_.)

Several catalog files are supplied with `toolshelf` itself; you can use
the following specification as a shortcut for
`@$TOOLSHELF/.toolshelf/catalog/collection.catalog`:

    toolshelf dock @@collection

♦ To better accommodate tab-completion, `toolshelf` should also allow you
to pass the `@` or `@@` as a seperate argument on the command line, like:

    toolshelf dock @ ~/gezbo.catalog

#### When referring to an already-docked source ####

When referring to a source which is already docked, a single source
specification may resolve to multiple sources.  Notably, the source
specification `all` refers to all sources which are currently docked:

    toolshelf build all

Several commands take `all` to be the default if no source spec is given.

To refer to all locally-docked source trees by a particular user, the
following syntax may be used:

    toolshelf build alincoln/all

When referring to a single source which is already docked, `toolshelf` allows
you to give just the source's base name, omitting the site name and the
user name.  For example, to build the first source we docked above, you
can say

    toolshelf build Gettysburg-Address

If more than one source has the same base name, the source specification
will resolve to all sources that have that base name.  You may supply the
username as well to resolve the ambiguity:

    toolshelf build alincoln/Gettysburg-Address

but an ambiguity may still occur, and the specification may refer to
multiple sources from multiple hosts.  In this case, you must add both the
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

If the source has a cookie that specifies a `build_command` hint, that
command will be used.  Otherwise...

If there is a script called `build.sh` or `make.sh`, it will run that.
Otherwise...

If there's an `autogen.sh` but no `configure`, it runs that first, to
create `configure`.

♦ If there's no `autogen.sh`, but there is a `configure.in`, it runs
`autconf` to create `configure`.

If there's a `configure`, it runs that, to create a `Makefile`.

If there's a `Makefile`, it runs `make`.

If there's a `build.xml`, it runs `ant` instead.

### "Cookies" ###

`toolshelf` comes with a (small) database of "cookies" which supplies extra
information (hints) about the idiosyncracies of particular, known projects.
As you discover idiosyncracies of new software you try to dock, you can add
new hints to this database (and open a pull request to push them upstream for
everyone to benefit from.)

The use of the term "cookie" here is not like "HTTP cookie" or "magic cookie",
but more like how it was used in Windows 3.1 (and may, for all I know, still
be used in modern Windows.)  Such cookies informed the OS about how to deal
with particular hardware for which the generic handling was not sufficient.
This usage of the word is apparently derived from the word "kooky" — that is,
idiosyncratic and non-standard.

In some ways, `toolshelf`'s cookies file is like the `Makefile`s used in
FreeBSD's package system — the information contained in it is similar.
However, it is just a single file, and is parsed directly instead of being a
`Makefile`.

The cookies file for `toolshelf` consists of a list of source specifications
with hints.  When `toolshelf` is given a source specification which matches
one in the cookies file, it automatically applies those hints.

Example of an entry in the cookies file:

    gh:user/project
      exclude_paths tests
      build_command ./configure --with-lighter-fluid --no-barbecue && make

The global shared cookies file which ships with `toolshelf` is located at
`$TOOLSHELF/.toolshelf/cookies.catalog`.  The file 
`$TOOLSHELF/.toolshelf/local-cookies.catalog` can be created and edited by
the user to supply their own local cookies; this file will not (and should not)
be checked in to the `toolshelf` repo (it's in `.gitignore` and `.hgignore`.)

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

*   `require_executables`
    
    Example: `require_executables perl`
    
    A space-separated list of executables required to dock and run the source.
    When this is given, `toolshelf` first checks if you have the named
    executable on your executable search path; if you do not, it will display
    an error message, and will not try to dock the source.
    
*   `rectify_permissions`
    
    Example: `rectify_permissions yes`

    Either `yes` or `no`.  If `yes`, rectify the execute permissions of the
    source, which means: after checking out the source but before building
    it, traverse all of the files in the source tree, run `file` on each one,
    and set its executable permission based on whether `file` called it
    `executable` or not.  This defaults to `no` for all sources except for
    `.zip` archives, for which it defaults to `yes`; this hint will override
    the default.
    
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
    
*   `build_command`
    
    Example: `build_command ./configure --no-cheese && make`
    
    A shell command that will be used to build the source.  `toolshelf`
    passes the entire hint value to the shell for execution.  The command
    will be run with the root of the source tree as the working directory.
    `toolshelf`'s built-in heuristics for building sources will not be used.

Theory of Operation
-------------------

This section describes how it all works — specifically, how typing
`toolshelf` can seemingly magically alter your search paths.

### `bootstrap-toolshelf.sh` ###

The bootstrap script does a few things:

- It checks that you have `git` and `python` installed.  If you don't, it asks
  you to install them, and stops.
- It asks you where you want to store source trees for the packages you dock
  using toolshelf; it calls this `$TOOLSHELF`.  The default is
  `$HOME/toolshelf`.
- It then clones the `toolshelf` git repo into `$TOOLSHELF/.toolshelf`.
- It then asks permission to modify your `.profile` or equivalent shell
  startup script.  If you decline, you are asked to make these changes
  manually.  It adds a line that sources (using `.`) `init.sh` (see below.)
- Finally, it `source`s `init.sh` itself, so that `toolshelf` is available
  immediately after bootstrapping (you don't need to start a new shell.)

### `init.sh` ###

The script `init.sh` initializes `toolshelf` for use; it is typically
sourced (using `.`) from within `.profile` (or equivalent shell startup
script.)  This is what it does:

-   Takes a single command-line argument, which is the `toolshelf` directory,
    and exports it as the `TOOLSHELF` environment variable
-   Puts `$TOOLSHELF/.toolshelf/bin` (where the `toolshelf` executable lives)
    and `$TOOLSHELF/.bin` (the link farm `toolshelf` will create) onto the
    shell's executable search path (`$PATH`.)
-   Defines a shell function called `toolshelf_cd`, which does the following:
    -   It runs `toolshelf pwd`, with the arguments that were passed to the
        `toolshelf_cd` function, in backticks.
    -   It attempts to `cd` to the output of `toolshelf pwd`.
    -   The `cd` is done in this shell function, because the `toolshelf`
        executable itself can't affect the user's shell.

The `toolshelf_cd` function and the `toolshelf.py` script, taken together,
perform something which we could call the "shell-then-source trick".  In
effect, it makes it possible for a "command" (really a shell function) to
affect the environment of the user's current interactive shell — something
an ordinarily invoked command cannot do.  This is what lets `toolshelf_cd`
change your current working directory.

### `toolshelf` ###

The executable Python script `toolshelf` finds the `toolshelf.py` module,
imports it, and runs the thing in it that does all the real work.

### `toolshelf.py` ###

The Python module `toolshelf.py` is the workhorse:

- It checks its arguments for an appropriate subcommand.
- For the subcommand `dock`, it expects to find a source specifier.  It parses
  that specifier to determine where it should find that source.  It attempts
  to obtain that source (using `git clone` or whatever) and places the source
  tree under a subdirectory (organized by domain name and user name) under
  `$TOOLSHELF`.  It then decides if the obtained source needs building, and if
  so, builds it.  It then calls `toolshelf relink` (internally) to rebuild the
  link farm.
- It checks for other arguments as needed.  Since it's trivial to remove a
  package that has been docked, there might not be a `undock` subcommand.
  (Actually there should be one that rebuilds the link farm afterwards.)

Loose `toolshelf` Integration
-----------------------------

If you want to write a "toolshelf plugin", or more literally, any Python program
that can optionally use functions from `toolshelf.py` when a toolshelf is in use,
you can use the following code:

    import os
    if 'TOOLSHELF' in os.environ and os.environ['TOOLSHELF']:
        sys.path.insert(0, os.path.join(
            os.environ['TOOLSHELF'], '.toolshelf', 'src'
        ))
        import toolshelf
    else:
        toolshelf = None

Then later on...

    if toolshelf:
        t = toolshelf.Toolshelf()
        t.dock(['gh:user/repo'])

Note that toolshelf is in constant flux, even if it is a slow flux, so don't
rely on this too heavily.
