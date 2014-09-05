import os

def show(shelf, args):
    specs = shelf.expand_docked_specs(args)
    sources = shelf.make_sources_from_specs(specs)
    for source in sources:
        # TODO: colourize the output for which are exes, which are dirs
        for (link_farm_name, link_farm) in shelf.link_farms.iteritems():
            for (linkname, filename) in link_farm.links():
                if filename.startswith(source.dir):
                    showname = filename.replace(shelf.dir, '$TOOLSHELF')
                    print "[%s] %s -> %s" % (
                        link_farm_name, os.path.basename(linkname), showname
                    )
                    if (link_farm is shelf.link_farms['bin'] and
                        (not os.path.isfile(filename) or
                         not os.access(filename, os.X_OK))):
                        print "BROKEN: %s is not an executable file" % filename
