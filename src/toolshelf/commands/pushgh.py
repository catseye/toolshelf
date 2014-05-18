def pushgh(shelf, args):
    """Push updates to a Github git mirror of a Mercurial repository.  Requires
    that the hg-git Mercurial extension has been set up.  Assumes that the name of
    the repository on Github is the same as the project name (luckily, Github is
    case insensitive about project names.)

    """
    def pushgh_it(source):
        shelf.run('hg', 'bookmark', '-f', '-r', 'tip', 'master')
        url = "git+ssh://git@github.com/%s/%s.git" % (source.user, source.project)
        shelf.run('hg', 'push', url)

    shelf.foreach_specced_source(
        shelf.expand_docked_specs(args), pushgh_it
    )
