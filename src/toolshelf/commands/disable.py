"""
Temporarily remove links to executables and libraries in specified sources.

The sources will be recorded in the persistent blacklist.

A subsequent `enable` will restore them.  Note
that this implies a `relink all` to make sure any previously-shadowed
links now show up with these sources disabled.

disable {<docked-source-spec>}

"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        shelf.blacklist.add(source)

    def trigger_relink(self, shelf):
        return ['all']
