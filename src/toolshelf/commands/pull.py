"""
Pull latest revision of specified sources from each's upstream repository.

Upstream repo is always the external source from which
it was originally docked.  Does not work on distfile-based sources.

pull {<docked-source-spec>}

"""

# TODO: figure out how to propogate was_changed to a subsequent 'build'

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def show_progress(self):
        return False

    def perform(self, shelf, source):
        source.update()
