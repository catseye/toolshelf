import os

def which(shelf, args):
    for farm in shelf.link_farms:
        for arg in args:
            linkname = os.path.join(shelf.link_farms[farm].dirname, arg)
            if os.path.islink(linkname):
                filename = os.readlink(linkname)
                print '[%s] %s' % (farm, filename)
