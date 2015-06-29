"""
Show the revision log of a docked source.

Does not work on distfile-based sources.

log {<docked-source-spec>}

"""

import os
from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def show_progress(self):
        return False

    def perform(self, shelf, source):
        shelf.chdir(source.dir)
        if os.path.isdir(os.path.join(source.dir, '.hg')):
            shelf.run('hg', 'log')
        elif os.path.isdir(os.path.join(source.dir, '.git')):
            shelf.run('git', 'log')
        else:
            raise NotImplementedError('source "%s" is not version-controlled' %
                                      source.name)
