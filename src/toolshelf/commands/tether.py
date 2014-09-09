from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def show_progress(self):
        return False

    def specs_are_external(self):
        return True

    def perform(self, shelf, source):
        if source.docked:
            print "%s already docked." % source.name
        else:
            source.checkout()
