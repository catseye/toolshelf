toolshelf - Theory of Operation
===============================

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
