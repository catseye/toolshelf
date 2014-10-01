"""
Restore any previously disabled links for the given sources.

enable {<docked-source-spec>}

The sources will be removed from the persistent blacklist.

"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        shelf.blacklist.remove(source)
        source.relink()
