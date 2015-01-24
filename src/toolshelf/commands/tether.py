"""
Obtain external source trees (repos or distfiles, from internet or filesystem).

{<external-source-spec>}
"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def show_progress(self):
        return False

    def specs_are_external(self):
        return True

    def perform(self, shelf, source):
        if source.docked:
            if source.tag:
                source.update_to_tag(source.tag)
            else:
                print "%s already docked." % source.name
        else:
            source.checkout()
            source.rectify_permissions_if_needed()
