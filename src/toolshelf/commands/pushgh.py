from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    """Push updates to a Github git mirror of a Mercurial repository.  Requires
    that the hg-git Mercurial extension has been set up.  Assumes that the name
    of the repository on Github is the same as the project name (luckily, Github
    is case insensitive about project names.)

    """
    def show_progress(self):
        return False

    def perform(self, shelf, source):
        shelf.run('hg', 'bookmark', '-f', '-r', 'tip', 'master')
        url = "git+ssh://git@github.com/%s/%s.git" % (source.user, source.project)
        shelf.run('hg', 'push', url)
