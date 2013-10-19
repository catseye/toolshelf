# `source` this script to convert your toolshelf installation to a development-
# bootstrapped toolshelf installation.  This is probably only useful if you
# develop on toolshelf itself; if you have no interest in that, you may stop reading.

# Normally, toolshelf keep a copy of the `toolshelf` repo at
# `$TOOLSHELF/.toolshelf`.  This script looks for a `toolshelf` repo that has
# been *docked* using toolshelf, and links that directory to that docked repo.

# This is kind of a dumb script but I assume that if you want to develop on
# toolshelf, you know what you're doing.  (Developing on toolshelf using a repo
# that is docked with toolshelf can also be tricky; you can paint yourself into
# a corner, and so forth.  Again, I assume you know what you are doing.)

DIR=`$TOOLSHELF/.toolshelf/bin/toolshelf pwd toolshelf`
mv $TOOLSHELF/.toolshelf $TOOLSHELF/.toolshelf-backup
ln -s $DIR $TOOLSHELF/.toolshelf
echo "Linked .toolshelf to $DIR"
