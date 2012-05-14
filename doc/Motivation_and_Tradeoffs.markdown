Why `toolshelf`?
================

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

Advantages
----------

* When it works, it's pretty slick.  Issue one command, and when it finishes,
  you can immediately issue new commands from the software you "installed".

* It doesn't clutter up the system directories, or your home directory.  You
  can remove a source tree (or the whole kit and kaboodle) with a single
  `rm -rf`, and you know you got everything.

* It encourages hackability.  The sources are there -- if you have a problem,
  go edit them.  If they're in a repo, you can commit and branch and restore
  a previous version and whatever.  If you have push privleges for an upstream
  repo, you can send your changes off there.

Limitations
-----------

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
