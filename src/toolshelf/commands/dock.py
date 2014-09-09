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
            # require_executables = source.hints.get(
            #     'require_executables', None
            # )
            # if require_executables:
            #     p = Path()
            #     for executable in require_executables.split(' '):
            #         if not p.which(executable):
            #             raise DependencyError(
            #                 '%s requires `%s` not found on search path' %
            #                 (source.name, executable)
            #             )
            source.checkout()
            source.rectify_permissions_if_needed()
            source.build()
            source.relink()
