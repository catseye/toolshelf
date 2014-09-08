from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    """Reports which docked source trees have changes that are not in the
    upstream repo.  Quite crude.

    """
    def perform(self, shelf, source):
        print source.name
        shelf.run('hg', 'out')
        #outgoing = shelf.get_it("hg out")
        #if 'no changes found' not in outgoing:
        #    print outgoing
