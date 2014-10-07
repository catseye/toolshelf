"""
Crudely reports docked sources that have changes not in the upstream repo.

"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        print source.name
        shelf.run('hg', 'out')
        #outgoing = shelf.get_it("hg out")
        #if 'no changes found' not in outgoing:
        #    print outgoing
