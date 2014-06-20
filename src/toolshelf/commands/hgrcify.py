import os

def hgrcify(shelf, args):
    def hgrcify_it(source):
        hg_dir = os.path.join(source.dir, ".hg")
        if not os.path.exists(hg_dir):
            shelf.warn("not a mercurial repo")
            return
        with open(os.path.join(hg_dir, "hgrc"), 'w') as f:
            f.write("[paths]\n")
            f.write("default = https://%s@%s/%s/%s" %
                    (source.user, source.host, source.user, source.project))

    shelf.foreach_specced_source(
        shelf.expand_docked_specs(args), hgrcify_it
    )
