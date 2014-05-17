`toolshelf` — Philosophical Points
==================================

Why `toolshelf`?
----------------

This section describes why I wrote `toolshelf`, and what it's aptitude's good
at and not so good at.

So, without further ado:

### This whole notion of "installing" ###

I've never liked the way that software is conventionally installed (especially
under Unix — I can't speak for Mac and I will disregard Windows here.)

There is this Unix command called `install`, see.  All it does is copy some
files from one place to another, and set some attributes on them.  But `cp`,
`chmod`, etc. already exist in Unix, and Unix is the poster child of gluing
together small utilities to do what you want, so why a seperate command?  For
that matter, why do these executable that I want to use *need* to be copied to
some other place anyway?

Mostly historical reasons.  Early computer systems didn't have a lot of
disk space, and disks weren't fast.  So it was advantageous to put all the
executables (and only the executables) that the users were going to use, into
one central place (or a couple of central places.  Aside: why are there seperate
`/usr/bin` and `/usr/sbin` directories?  So that if you accidentally ran
`rm -rf /usr/*`, you could `^C`-it before it got to `sbin` — or so I've heard.)

That situation of constrained resources is no longer the case.  Unix systems
can efficiently search the `$PATH` to find executables.  But it is
definitely still the habit of developers who distribute their software to
write an `install` target in their `Makefile` (which is a `.PHONY` target
and thus antithetical to the purpose of `make`, but that's another story.)

It disappoints me everytime I see a project on Github that tells you to
`sudo make install` it.  Like, I'm sure your `install` target is perfectly
bug-free and non-malicious, stranger, but I'd still rather not give it
`root` priviledges just so it can copy some executables from one place in
the filesystem to a bunch of other places in the filesystem (`/usr/bin`,
`/usr/lib`, `/usr/share/`, ...), *without even recording what it installed
where.*  Did you write a `make uninstall` target?  No?  OK, then you're
basically asking me to pollute my system.  Because, in practice, this sort
of action leads to having a system with a bunch of "space junk" in it that
will never get cleaned up.  It might go unnoticed most of the time... until
there's a collision, that is...

Of course, this is (or would be) partly my fault for believing the project
docs when they parrot the cargo-cult instructions "next, run `make install`."
Often, the software will work just fine, even if I just build it and don't
install it.  (Not always, of course, but often.)  The main problem remaining
is being able to use it without having to remember where it's located;
but to solve this, all I have to do is to learn to adjust my `$PATH`.

### Package managers ###

So yeah, people have tried to solve this problem by distributing software
in packages, with a tool called a "package manager" that can install
software, uninstall it (correctly, we hope,) and track the dependencies
between packages so you know what else you need when you want to install
something.

And yeah, package managers reduce a lot of the pain of installing software.
They do.  I'm not faulting them.  But they create new pains.

Package managers create a whole new class of labour -- package maintainers.
Release engineering is one thing, but this really shouldn't be a specialized
skill, you know?  And the package maintainer probably has a slightly different
idea of how the package should be installed — different from how the
developers thought it should be installed

Package managers are generally tied to a platform.  So, if you use Ubuntu,
and your system has bits written in Python and Ruby and Haskell and Node.js,
how many package managers will you use?  `apt`, Pypi, gems, Cabal, and `npm` —
that's five.  Will some of the language-specific packages also be available
in the OS-specific package manager?  Oh, definitely.  Will you mix them?
Erm, probably not the best idea.  OK, so will you use only the OS-level
packages?  Erm, well they don't get updated as quickly...

...besides, there's this one patch we really need to apply, and no one's
heard from the maintainer in months, so...

Basically, a package manager is an attempt to solve the problem by creating
a *closed system* of a sort.  The problem is that closed systems are an
uphill battle against chaos.

And the whole concept is still built on top of the "installation" concept
anyway.

### So. ###

There is lots more I could rant about, but I'll leave it at here for now.

So, faced with all this — exploring random projects on Github and wanting
to try them out without installing them; battling package managers almost
as much as battling the system when building from source; and not wanting
to learn the details and idiosyncracies of a different package manager for
every platform —

Faced with all this, I got into the habit of installing everything in my
home directory.  At least then, I could blow away my home directory if I
wanted to clean everything up.  For distributions that include a `configure`
script or similar, this is usually as easy as specifying `--prefix=$HOME`
as an argument to it — then making sure `$HOME/bin` is on your path, and
perhaps `$HOME/lib` is added to your `LD_LIBRARY_PATH`.

But even then, things in `$HOME/bin` can conflict with my personal scripts,
and after enough installs, my home directory is basically impossible to clean
up too.  And, although I could, I don't really want to blow it away (I mean...
it *is* my home directory, after all.)

So I decided I should write `toolshelf`.


Advantages of `toolshelf`
-------------------------

*   Doesn't require superuser priviledges just to copy some files from one
    place to another.

*   It doesn't clutter up the system directories, or your home directory.  You
    can remove a source tree (or the whole kit and kaboodle) with a single
    `rm -rf`, and you know you got everything.  (Except the symlinks, but
    those are generally harmless, and easy to clean up: `toolshelf relink all`.)

*   There is no such thing as a "missing package" — if the software is on the
    Internet somewhere in a common format (Git repository, tarball, etc.),
    you can dock it with `toolshelf`.  There is no package metadata to go out
    of date.  There is no package database to get corrupted.  There is no
    package maintainer to go missing.

*   It encourages hackability.  The sources are there — if you have a problem,
    go edit them.  After you rebuild, the new executable will immediately be
    on your `$PATH` — no install step.  If the docked sources are in a repo,
    you can commit and branch and restore a previous version and whatever.
    If you have push privleges for an upstream repo, you can send your changes
    off there.


Limitations of `toolshelf`
--------------------------

*   It doesn't, and can't be expected to, work for every piece of software
    out there.

    *   The array of possible build tools that are used by small, experimental
        software distributions is huge — too large for `toolshelf`'s heuristics
        to ever realistically encompass.  It handles the most common ones
        (`autoconf`, `make`, and the like.)
                
    *   Small, experimental software distributions don't always include an
        automated build procedure, just instructions for a human, and
        `toolshelf` obviously can't follow those.
    
    It makes its best guess at how to build, but you can't expect `toolshelf`
    to "just work" in any case that's not well-trodden.  On the other hand,
    
    *   If you were going to install from source without `toolshelf`, you'd
        have to fiddle with your build environment anyway, so it's no worse
        than that.
    
    *   If the software developer has written their build system in a
        reasonable (or even just traditional) manner, `toolshelf`'s
        heuristics *can* detect it and use it.

*   It's at its best for small, experimental software distributions — the
    kind you might want to play with, but maybe not keep around forever.
    It was not designed to replace your OS's package manager.  (That said,
    it *is* often able to install "infrastructure" packages like language
    interpreters.)

*   It doesn't track dependencies.  It's up to you to know what the software
    you want to dock requires, and to dock or install that required software
    first.  And you must use caution when upgrading — if you upgrade one of
    your docked sources, anything else you have docked that relies on a
    previous might break.

*   Some executables load resources, and expect those resources to be in
    certain locations.  If the executable looks for those resources in locations
    that are relative to the path to the executable, that's good; the executable
    and the resources will both be in the docked source, and it should find
    them.  Or, if it looks for them on a search path, that's also not so bad.
    Or, sometimes the path is "burned into" the executable during a `configure`
    step — this makes my skin crawl a little bit, but it's acceptable in the
    sense that `toolshelf` can handle it.
    
    But sometimes they look for resources relative to the current working
    directory — in which case there's little point being able to invoke the
    executable, from the search path, while in another directory.  And if they
    look for resources in fixed locations, like `/usr/share/`, well, that's an
    outgrowth of old habits, and really not so good.  There's not a lot one can
    do about that, aside from maybe forking the project and fixing it.

*   Building from source can take a lot of time and resources.  (Of course,
    there's nothing saying you *have* to build from source — there is nothing
    in theory that prevents you from docking a tarball containing a pre-built
    executable.  But it's really designed for source distributions.)

*   Support for docking the same source under multiple operating systems is
    not so hot.  I'll rant about this sometime.  It usually falls under
    writing the build system in a reasonable manner; requiring you to
    run `make linux` on a Linux system but `make bsd` on a FreeBSD system,
    is actually not entirely reasonable.  (I'm thinking of Lua and CHICKEN
    Scheme here.)


Case Studies
------------

This is just a sampling of sources I've tried with `toolshelf` so far, and
description of how well they work with the `toolshelf` model, and why.

*   `toolshelf dock `[`gh:nelhage/reptyr`][]
    
    `reptyr` is a Linux utility, written in C, for attaching an already-running
    process to a GNU `screen` session.  It lives in a github repo.  Because it's
    Linux-specific, its build process is simple and `toolshelf` has no problem
    figuring out how to build it and put it on the executable search path.

*   `toolshelf dock `[`bb:catseye/yucca`][]
    
    `yucca` is a Python program for performing static analysis on 8-bit BASIC
    programs.  Because it's written in Python, it doesn't need building, and
    because it has no dependencies on external Python libraries, it doesn't need
    anything besides Python to run.
    
    `yucca` is hosted on Bitbucket, with a git mirror on github; `toolshelf`
    can obtain the source from either site, using Mercurial or git respectively.

*   `toolshelf dock `[`gh:kulp/tenyr`][]

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
    
*   `toolshelf dock `[`http://ftp.gnu.org/gnu/bison/bison-2.5.tar.gz`][]
    
    Is your system `bison` version 2.4, but you need version 2.5 installed
    temporarily in order to build `kulp/tenyr`?  No problem; just put it on
    your `toolshelf` with the above command.  After it's docked, you can issue
    the commands `toolshelf disable ftp.gnu.org/bison-2.5` and
    `toolshelf enable ftp.gnu.org/bison-2.5` to remove or reinstate
    it from your search path, respectively.  Similar to `tenyr`, this source has
    the hint `exclude_paths tests etc examples build-aux` associated with it.

[`gh:nelhage/reptyr`]: https://github.com/nelhage/reptyr
[`bb:catseye/yucca`]: https://bitbucket.org/catseye/yucca
[`gh:kulp/tenyr`]: https://github.com/kulp/tenyr
[`http://ftp.gnu.org/gnu/bison/bison-2.5.tar.gz`]: http://www.gnu.org/software/bison/bison.html
