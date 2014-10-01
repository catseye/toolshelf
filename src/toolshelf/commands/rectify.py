"""
rectify {<docked-source-spec>}

Traverses the file trees of the given docked source and modifies the
permissions of files, removing or adding the executable bit based on
whether toolshelf thinks the file should really be executable or not.
"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        source.rectify_executable_permissions()
