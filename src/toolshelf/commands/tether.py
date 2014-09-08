from toolshelf.toolshelf import BaseCommand

# FIXME do not actually expand_docked_specs

class Command(BaseCommand):
    def perform(self, shelf, source):
        if source.docked:
            print "%s already docked." % source.name
        else:
            source.checkout()
