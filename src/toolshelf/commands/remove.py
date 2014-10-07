"""
Delete the specified source trees and relink all remaining docked sources.
"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        shelf.run('rm', '-rf', source.dir)

    def trigger_relink(self, shelf):
        return ['all']
