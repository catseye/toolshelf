"""
build {<docked-source-spec>}

Build (or re-build) the executables for the specified docked sources.
"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def show_progress(self):  # only if quiet
        return False

    def perform(self, shelf, source):
        source.build()
