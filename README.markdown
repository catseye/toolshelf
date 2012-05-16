toolshelf
=========

`toolshelf` is a "package manager" which doesn't actually install any files.
Instead, it stores the source trees of sundry packages in a single directory,
and manages your search paths to include the relevant subdirectories of those
trees.  The source trees are typically the working directories of local `git`
or Mercurial clones, or they can be source distributions from tarballs.

`toolshelf` requires that you use `bash` as your shell.  It also requires
Python to run the workhorse script.

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

Further Reading
---------------

For the closest thing we have to a reference manual right now, just run
`toolshelf` without arguments.

See [Heuristics and Cookies][] for how `toolshelf` goes about figuring out
where it should grab the source from, how it should build it, and what it
should put on your search paths; and how you can influence it when it's not
clever enough to figure these things out by itself.

See [Motivation and Tradeoffs][] for why I wrote `toolshelf`, and what it's
aptitude's good at and not so good at.

See [Theory of Operation][] for how it works -- specifically, how typing
`toolshelf` can seemingly magically alter your search paths.

See [doc/Success_Stories.markdown](https://github.com/catseye/toolshelf/blob/master/doc/Success_Stories.markdown)
for some sources which have turned out to work remarkably well with
`toolshelf`.

[Heuristics and Cookies]: https://github.com/catseye/toolshelf/blob/master/doc/Heuristics_and_Cookies.markdown
[Motivation and Tradeoffs]: https://github.com/catseye/toolshelf/blob/master/doc/Motivation_and_Tradeoffs.markdown
[Theory of Operation]: https://github.com/catseye/toolshelf/blob/master/doc/Theory_of_Operation.markdown

License
-------

`toolshelf` is placed under an MIT-style license.

Related Work
------------

* `sources`

* `zero-install`/`0launch`

* `checkoutmanager`

