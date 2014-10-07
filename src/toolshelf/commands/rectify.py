"""
Traverse sources and set executable permissions 'reasonably' on all files.

rectify {<docked-source-spec>}
"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        source.rectify_executable_permissions()
