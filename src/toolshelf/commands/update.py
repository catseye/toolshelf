from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def perform(self, shelf, source):
        was_changed = source.update()
        if was_changed:
            source.build()
            source.relink()
