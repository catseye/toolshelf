
def index(shelf, args):
    specs = shelf.expand_docked_specs(args)
    sources = shelf.make_sources_from_specs(specs)
    for source in sorted(sources, key=lambda s: s.name):
        print source.name
