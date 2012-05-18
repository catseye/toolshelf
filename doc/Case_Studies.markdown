Case Studies
============

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
