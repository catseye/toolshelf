Why `toolshelf`?
----------------

This section describes why I wrote `toolshelf`, and what it's aptitude's good
at and not so good at.

I've always been a little disturbed by the practice of running something like
`sudo make install` and having it write files into a whole bunch of places
in your filesystem — `/usr/bin` (or `/usr/local/bin` or `/usr/pkg/` depending
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
to it — then making sure `$HOME/bin` is on your path, and perhaps `$HOME/lib`
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

* It encourages hackability.  The sources are there — if you have a problem,
  go edit them.  If they're in a repo, you can commit and branch and restore
  a previous version and whatever.  If you have push privleges for an upstream
  repo, you can send your changes off there.

### Limitations ###

* It doesn't always work, and can't always work for every piece of software
  out there.

* It's at its best for small, experimental software distributions — the
  kind you might want to play with, but maybe not keep around forever.
  It's not designed for real meat-and-potatoes system software.  So, for
  example, if a package is written in Ruby, docking that package is not
  going to install Ruby for you if it's not already installed; the onus is on
  you to install Ruby if the package needs it.

* The array of possible build tools that are used by small, experimental
  software distributions is huge — too large for `toolshelf`'s heuristics
  to ever realistically encompass.  It handles the most common ones
  (`autoconf`, `make`, and the like.)

* Small, experimental software distributions don't always include an automated
  build procedure, just instructions for a human, and `toolshelf` obviously
  can't follow those.

* Taking the previous two points together, you can't expect `toolshelf` to
  "just work" in any case that's not well-trodden.  (On the other hand, if
  you were going to install from source without `toolshelf`, you'd have to
  fiddle with your build environment anyway, so it's no worse than that.)

* Some executables load resources, and expect those resources to be in
  certain locations.  If the executable looks for those resources in locations
  that are relative to the path to the executable, that's good; the executable
  and the resources will both be in the docked source, and it should find
  them.  Or, if it looks for them on a search path, that's also not so bad.
  But sometimes they look for resources relative to the current working
  directory — in which case there's little point being able to invoke the
  executable, from the search path, while in another directory.  (`toolshelf`
  may one day grow a feature to handle this.)  And if they look for resources
  in fixed locations, well, that's not so good, and there's not a lot one can
  do about that, aside from maybe forking the project and fixing it.

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
