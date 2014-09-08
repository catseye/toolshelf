import os

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        shelf.run('rm', '-rf', source.dir)

    def teardown(self, shelf):
        # TODO this should just be a 'needs relinking' thing that
        # BaseCommand handles itself (could be common to multiple commands)
        shelf.relink(['all'])
