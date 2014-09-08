import os

from toolshelf.toolshelf import BaseCommand

def remove(shelf, args):
    def remove_it(source):
        shelf.run('rm', '-rf', source.dir)

    shelf.foreach_specced_source(
        shelf.expand_docked_specs(args), remove_it
    )
    shelf.relink(['all'])


class Command(BaseCommand):
    def perform(self, shelf, source):
        shelf.run('rm', '-rf', source.dir)

    def teardown(self, shelf):
        # TODO this should just be a 'needs relinking' thing that
        # BaseCommand handles itself (could be common to multiple commands)
        shelf.relink(['all'])
