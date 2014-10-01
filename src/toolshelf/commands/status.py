"""
status {<docked-source-spec>}

Show the `hg status` or `git status`, as appropriate, in their
naive format, for the given docked sources.  Does not work for
distfile-based sources.
"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def show_progress(self):
        return False

    def perform(self, shelf, source):
        source.status()
