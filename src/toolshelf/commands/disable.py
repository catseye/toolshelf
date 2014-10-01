"""
disable {<docked-source-spec>}

Temporarily remove the links to executables in the given docked projects
from your link farm.  A subsequent `enable` will restore them.  Note
that this implies a `relink all` to make sure any previously-shadowed
links now show up with these sources disabled.
"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        shelf.blacklist.add(source)

    def trigger_relink(self, shelf):
        return ['all']
