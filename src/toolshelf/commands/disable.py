from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        self.blacklist.add(source)

    def teardown(self, shelf):
        shelf.relink(['all'])
