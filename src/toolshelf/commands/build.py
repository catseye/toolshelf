from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def show_progress(self):  # only if quiet
        return False

    def perform(self, shelf, source):
        source.build()
        source.relink()
