from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        shelf.blacklist.remove(source)
        source.relink()
