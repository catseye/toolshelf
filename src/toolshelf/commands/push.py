"""
Push changes from specified sources to each's upstream repository.

Upstream repo is always the external source from which
it was originally docked.  Does not work on distfile-based sources.

push {<docked-source-spec>}

"""

import os

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def show_progress(self):
        return False

    def perform(self, shelf, source):
        shelf.chdir(source.dir)
        if os.path.isdir('.git'):
            shelf.run('git', 'push', 'origin')
        elif os.path.isdir('.hg'):
            shelf.run('hg', 'push', '-r', 'tip')
            # TODO: if the output contains 'no changes found',
            # a failure-exit code is to be expected
        else:
            raise NotImplementedError(
                "Can't push a non-version-controlled Source"
            )
