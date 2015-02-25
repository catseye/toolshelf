"""
Push updates to an alternative toolshelf.

Requires that the environment variable ALT_TOOLSHELF is defined.

This is rather a hack and should be handled more elegantly in a future version.

"""

import os

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def show_progress(self):
        return False

    def perform(self, shelf, source):
        alt_toolshelf = os.getenv('ALT_TOOLSHELF', None)
        assert alt_toolshelf is not None
        upstream = os.path.join(alt_toolshelf, source.name)

        shelf.chdir(source.dir)
        if os.path.isdir('.git'):
            shelf.run('git', 'push', upstream)
        elif os.path.isdir('.hg'):
            shelf.run('hg', 'push', upstream)                
        else:
            raise NotImplementedError(
                "Can't push a non-version-controlled Source"
            )
