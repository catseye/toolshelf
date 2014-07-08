import os

def resolve(shelf, args):
    def resolve_it(source):
        print source.dir

    shelf.foreach_specced_source(
        shelf.expand_docked_specs(args), resolve_it
    )
