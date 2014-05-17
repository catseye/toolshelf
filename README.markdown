toolshelf
=========

First, the metaphor:

Certain bulky technologies in your home — such as your washing machine and your
refrigerator (let's call them appliances) — deserve to be *installed*.  You're
not going to move them much, and they might have to be hooked up to the water
pipes and so forth.

But certain other, lighter technologies — such as your can opener and your 
broom and dustpan (let's call them tools) — aren't "installed" anywhere.
Instead, you simply store them somewhere (say, on a shelf) until they're needed.

`toolshelf` applies this paradigm to software.  Because you should never need to
*install* a can opener.

If this metaphor piques your curiosity, you can read more about
[why `toolshelf` exists](https://github.com/catseye/toolshelf/blob/master/doc/Philosophy.markdown).

Description
-----------

`toolshelf` is a "package manager" which doesn't actually install any files.
Instead, it:

*   stores ("docks") the source distributions of projects in a directory tree
    (usually located in your home directory);
*   builds executables, libraries, etc. as needed in these source directories;
*   creates "link farms" of symlinks to these executables, libraries, etc.; and 
*   manages your search paths to include these link farms.

The source distributions are typically version-controlled working directories
(e.g. a local clone of a Git repository), but they can also be directory
structures extracted from downloaded archives (so-called "tarballs" or
"distfiles".)

`toolshelf` is a **work in progress**, currently **version 0.1-PRE**, and
subject to change.  It is written in Python 2.7, with some supporting scripts
in vanilla `sh`.  It also requires the presence of those tools it needs to use
to get and build what it asks for.  Obviously, the less you ask for, the less it
needs, but at least some of the following will be helpful:

*   `git` or `hg` (Mercurial)
*   `wget`
*   `tar` and `gzip` and/or `bzip2`
*   `unzip`
*   `make`

(It is also probably better if you use a POSIX `sh`-based shell, such as `bash`
or `ash`, as your interactive shell; otherwise you may lack some functions
such as `toolshelf_cd`.  I have not tested it with `csh`, `zsh`, etc.)

`toolshelf` is distributed under an MIT-style license.

Quick Start
-----------

*   Start a shell.  (On some OS'es, this means "Open a Terminal window.")
    
*   Download [`bootstrap-toolshelf.sh`][], for example by running:
  
        wget https://raw.github.com/catseye/toolshelf/master/bootstrap-toolshelf.sh
    
    (If you don't have `wget` installed, `curl` should also work.  Or you can
    just download it from the link above with your web browser.)
    
*   Run:
    
        . ./bootstrap-toolshelf.sh
    
*   Follow the instructions given to you by the script.

[`bootstrap-toolshelf.sh`]: https://raw.github.com/catseye/toolshelf/master/bootstrap-toolshelf.sh

(If you don't want to use the bootstrap script, it's not very difficult to
get toolshelf up and running manually; see below for instructions.)

Now, you can dock any source that `toolshelf` can handle, simply by typing,
for example,

    toolshelf dock gh:nelhage/reptyr

When that completes, you can run `reptyr` by simply typing

    reptyr

Convenient!  And if you want to `cd` to where the `reptyr` sources are, to
hack on it or whatever, just

    toolshelf_cd reptyr

And if you ever want to get rid of (almost) all trace of `reptyr` from your
system, simply run

    rm -rf $TOOLSHELF/nelhage/reptyr

(For removal to be completely complete, you'd also want to run
`toolshelf relink all`, to remove the now-broken symbolic links to the
executable(s) that were in `$TOOLSHELF/nelhage/reptyr`.)

And, if you want to get rid of (almost) all trace of `toolshelf` and all of
the packages you've docked using it, simply

    rm -rf $TOOLSHELF

(For removal to be completely complete, you'd also want to remove the commands
that `bootstrap-toolshelf.sh` added to your `.bashrc`.  But if your `$TOOLSHELF`
directory doesn't exist, they won't run anyway.)

If you want to know more, you can read more about
[how `toolshelf` works](https://github.com/catseye/toolshelf/blob/master/doc/Theory_of_Operation.markdown).

Manual Setup
------------

*   Decide where you want your toolshelf sources to be kept.  I keep mine
    in a directory called `toolshelf` in my home directory.  In the following
    examples, I'll use `/home/user/toolshelf`.  It is strongly recommended
    that this pathname not contain any spaces or other characters which
    normally require escaping for the shell; even if `toolshelf` handles all
    these cases correctly, there's a fair chance any random source that you
    dock won't.
    
*   Make this directory:
    
        mkdir -p /home/user/toolshelf
    
*   Clone the `toolshelf` repo into `.toolshelf` in it, perhaps like so:
    
        git clone https://github.com/catseye/toolshelf /home/user/toolshelf/.toolshelf
    
    If you prefer, you could use Mercurial and clone it from Bitbucket.
    Or get a zip of the `toolshelf` distribution, and unzip it to there.  Any
    of these options should be fine.

*   Add the following line to your `.profile`, or `.bash_profile`, or
    `.bashrc`, or the startup script for whatever POSIX-compliant Bourne
    shell-alike you use:
    
        export TOOLSHELF=/home/user/toolshelf/ && . $TOOLSHELF/.toolshelf/init.sh

*   Start a new shell and test that it works.

Related Work
------------

*   [checkoutmanager](https://bitbucket.org/reinout/checkoutmanager)
*   [Gobolinux](http://gobolinux.org/)
*   [pathify](https://github.com/kristi/pathify)
*   [sources](https://github.com/trentm/sources)
*   [spackle](https://github.com/kristi/spackle)
*   `zero-install`/`0launch`
*   `pkgviews`
