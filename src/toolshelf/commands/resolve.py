"""
Emit the names of the directories of the docked sources.

resolve {<docked-source-spec>}
"""

import os

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    """Output the absolute directory name(s) of the specified source(s)."""

    def show_progress(self):
        return False

    def perform(self, shelf, source):
        print source.dir
