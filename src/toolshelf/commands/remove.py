import os

def remove(shelf, args):
    def remove_it(source):
        shelf.run('rm', '-rf', source.dir)

    shelf.foreach_specced_source(
        shelf.expand_docked_specs(args), remove_it
    )
    shelf.relink(['all'])
