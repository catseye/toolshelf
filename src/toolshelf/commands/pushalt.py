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

        if os.path.isdir('.git'):
            # can't push directly to another git repo in the filesystem, b/c
            # "updating the current branch in a non-bare repository is denied",
            # so we cd there and pull from the main one instead.
            shelf.chdir(upstream)
            shelf.run('git', 'pull', source.dir, 'master')
        elif os.path.isdir('.hg'):
            shelf.chdir(source.dir)
            shelf.run('hg', 'push', upstream)                
        else:
            raise NotImplementedError(
                "Can't push a non-version-controlled Source"
            )
