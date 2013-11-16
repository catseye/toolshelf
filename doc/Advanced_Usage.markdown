Advanced Usage
==============

It is possible to use toolshelf without having Python, git,
Mercurial, or wget installed.  However, you have to perform
some steps manually.  Also, probably the first thing you'll
want to install, using "manual toolshelf", is Python.

Luckily, you can install Python under toolshelf.

I'll assume you want to use `/home/user/toolshelf` as your
toolshelf.  First,

    mkdir -p /home/user/toolshelf
    mkdir -p /home/user/toolshelf/.bin
    mkdir -p /home/user/toolshelf/localhost/distfile

Then, get copies of the toolshelf and Python distributions
onto your system somehow... perhaps download these and burn
them to a CD-ROM, or whatever:

    https://github.com/catseye/toolshelf/archive/master.zip
    http://www.python.org/ftp/python/2.7.6/Python-2.7.6.tgz

I'll assume these distfiles are present in `/cdrom/`.  Now,

    unzip /cdrom/toolshelf-master.zip
    mv toolshelf-master /home/user/toolshelf/.toolshelf
    cd /home/user/toolshelf/localhost/distfile
    tar zxvf /cdrom/Python-2.7.6.tgz
    cd Python-2.7.6
    ./configure --prefix=`pwd` && make && make install

And go do something else for a while, whilst Python builds.
Then:

    ln -s /home/user/toolshelf/localhost/distfile/Python-2.7.6/bin/python /home/user/toolshelf/.bin/python

Then edit your `.profile`:

    export TOOLSHELF=/home/user/toolshelf && . $TOOLSHELF/init.sh

Then start a new shell.  Then test that you can run python
and toolshelf:

    python -v
    toolshelf

If you can, great.  You can start off with

    toolshelf relink all

and this will add the other executables from the Python source
onto the source path.  *Note*, don't do a `make clean` in the
Python source directory, or you may not be able to use
`toolshelf` (the `python` binary will still be there, but the
`select` module will be deleted.)

You ought to be able to use `toolshelf` normally from this
point on.
