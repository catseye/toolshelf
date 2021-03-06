"""
Remove broken links from link farms.
"""

import os

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def process_args(self, shelf, args):
        for (name, farm) in shelf.link_farms.iteritems():
            for (linkname, sourcename) in farm.links():
                if not os.path.exists(sourcename):
                    shelf.note(
                        '`%s` does not exist, deleting `%s`...' %
                        (sourcename, linkname)
                    )
                    os.unlink(linkname)
        return []
