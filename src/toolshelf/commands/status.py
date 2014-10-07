"""
Show `hg st` or `git status` as appropriate for specified sources.

status {<docked-source-spec>}

Does not work fordistfile-based sources.

"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def show_progress(self):
        return False

    def perform(self, shelf, source):
        source.status()
