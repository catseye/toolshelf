toolshelf
=========

(**NOTE**: `toolshelf` is still very much a WIP; don't expect it to work yet)

`toolshelf` is a "package manager" which doesn't actually install any files.
Instead, it stores the source trees of sundry packages in a single directory,
and manages your search paths to include the relevant subdirectories of those
trees.  The source trees are typically the working directories of local `git`
clones, but other DVCS's could be accommodated, as could source distributions
from tarballs.

`toolshelf` requires that you use `bash` as your shell.  It also requires
Python to run the workhorse script.

Quick Start
-----------

1. Download this file and save it somewhere:
   `https://raw.github.com/catseye/toolshelf/master/bootstrap-toolshelf.sh`
2. Start a `bash` shell (if you haven't already) and change to the directory
   where you downloaded `bootstrap-toolshelf.sh`.
3. Run `source bootstrap-toolshelf.sh`.
4. Follow the instructions given to you by the script.

Now, when you want to "install" a package that `toolshelf` can handle, for
example `catseye/yucca`, you simply type

    toolshelf dock catseye/yucca

...and when that completes, you can run `yucca` by simply typing

    yucca

...and if you ever want to get rid of `yucca` from your system, simply

    rm -rf ${TOOLSHELF}/yucca

...and if you want to get rid of (almost) all trace of `toolshelf` and all of
the packages you've docked using it, simply

    rm -rf ${TOOLSHELF}

Why was `toolshelf` written?
----------------------------

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

But even then, `$HOME/bin` conflicts with my personal scripts, and after
enough installs, my home directory is basically impossible to clean up.  And,
although I could, I don't really want to blow it away (I mean... it *is* my
home directory, after all.)

So I decided I should write `toolshelf`.

So this solves everything, right?
---------------------------------

No, there are definite limitations.  `toolshelf` is designed for all those
small, experimental distributions you might want to play with, then get rid
of; it's not designed for real meat-and-potatoes system software.  So, for
example, if a package is written in Ruby, docking that package is not
going to install Ruby for you if it's not already installed; the onus is on
you to install Ruby if the package needs it.

How does it work?
-----------------

The bootstrap script does a few things:

- It checks that you have `git` and `python` installed.  If you don't, it asks
  you to install them, and stops.
- It asks you where you want to store source trees for the packages you dock
  using toolshelf; it calls this `$TOOLSHELF`.  The default is
  `$HOME/toolshelf`.
- It then clones the `toolshelf` git repo into `$ZERODIR/toolshelf`.
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

The script `toolshelf.sh` does one thing, and does it well:

- It runs `$TOOLSHELF/toolshelf/toolshelf.py`, with the arguments that were
  passed to `toolshelf.sh`, expecting it to output a temporary file -- then
  it `source`s that temporary file and deletes it.

The Python script `toolshelf.py` is the workhorse:

- It checks its arguments for `install` and a package name.  It looks for that
  package in its configuration file.  If found, it obtains that package
  (using `git clone` or whatever) and places it in `$TOOLSHELF`.
  It then decides if the obtained package needs building, and if so, builds
  it.  It then calls `toolshelf path rebuild` (internally) to rebuild the
  path.
- It checks its arguments for `path rebuild`, and if that was the subcommand,
  it rebuilds the `PATH` environment variable, and outputs the command
  `export PATH={{path}}`.  (`toolshelf.sh` `sources` this to make the new path
  available to your shell immediately.)
- It checks for other arguments as needed.  Since it's trivial to remove a
  package that has been docked, there might not be a `undock` subcommand.
