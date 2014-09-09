import os

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def show_progress(self):
        return False

    def perform(self, shelf, source):
        source.status()
