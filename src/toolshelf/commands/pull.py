"""
pull {<docked-source-spec>}

Pull the latest revision of the specified docked sources from each's
upstream repository (which is always the external source from which
it was originally docked.)  Does not work on distfile-based sources.
"""

# TODO: figure out how to propogate was_changed to a subsequent 'build'

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def show_progress(self):
        return False

    def perform(self, shelf, source):
        source.update()
