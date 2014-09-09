from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        self.blacklist.add(source)

    def trigger_relink(self, shelf):
        return ['all']
