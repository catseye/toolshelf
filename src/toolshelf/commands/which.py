import os

def which(shelf, args):
    for arg in args:
        linkname = os.path.join(shelf.bin_link_farm.dirname, arg)
        if os.path.islink(linkname):
            filename = os.readlink(linkname)
            print filename
