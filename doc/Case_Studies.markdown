Case Studies
============

This is just a sampling of sources I've tried with `toolshelf` so far, and
description of how well they work with the `toolshelf` model, and why.

* [`nelhage/reptyr`](https://github.com/nelhage/reptyr)

  `reptyr` is a Linux utility, written in C, for attaching an already-running
  process to a GNU `screen` session.  It lives in a github repo.  Because it's
  Linux-specific, its build process is simple and `toolshelf` has no problem
  figuring out how to build it and put it on the executable search path.

* [`catseye/yucca`](https://github.com/catseye/yucca)

  `yucca` is a Python program for performing static analysis on 8-bit BASIC
  programs.  Because it's written in Python, it doesn't need building, and
  because it has no dependencies on external Python libraries, it doesn't need
  anything besides Python to run.

  `yucca` is hosted on Bitbucket, with a git mirror on github; `toolshelf` can
  obtain the source from either site, using Mercurial or git respectively.
