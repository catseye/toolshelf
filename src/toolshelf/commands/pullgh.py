"""
Pull updates from a Github git mirror of a Mercurial repository.

Requires that the hg-git Mercurial extension has been set up.  Assumes
that the name of the repository on Github is the same as the project name
(luckily, Github is case insensitive about project names.)
"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def show_progress(self):
        return False

    def perform(self, shelf, source):
        url = "git+ssh://git@github.com/%s/%s.git" % (source.user, source.project)
        shelf.run('hg', 'pull', '-u', url)
