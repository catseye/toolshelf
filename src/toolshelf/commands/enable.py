"""
enable {<docked-source-spec>}

Restore links to executables for the given docked projects, previously
disabled.
"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        shelf.blacklist.remove(source)
        source.relink()
