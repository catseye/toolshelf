"""
Update link farms to contain links to executables and libraries in sources.

{<docked-source-spec>}
"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        source.relink()
