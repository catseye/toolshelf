"""
Echo the latest tag in a docked source.
"""

import os
import re

from toolshelf.toolshelf import BaseCommand


class Command(BaseCommand):
    """Echo the latest tag in a docked source."""

    def show_progress(self):
        return False

    def perform(self, shelf, source):
        print source.get_latest_release_tag()
