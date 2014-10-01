"""
relink {<docked-source-spec>}

Update your link farms to contain links to available executables and
libraries inside the specified docked sources.
"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        source.relink()
