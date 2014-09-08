import os

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    """Reports which docked source trees have changes that are not in the
    upstream repo.  Quite crude.

    """
    def perform(self, shelf, source):
        dest_dir = os.path.join(shelf.options.output_dir, source.name)
        if os.path.isdir(dest_dir):
            shelf.chdir(source.dir)
            if os.path.isdir(os.path.join(source.dir, '.hg')):
                shelf.run('hg', 'push', dest_dir, ignore_exit_code=True)
            elif os.path.isdir(os.path.join(source.dir, '.git')):
                shelf.run('git', 'push', dest_dir, ignore_exit_code=True)
            else:
                raise NotImplementedError('source "%s" is not version-controlled' %
                                          source.name)
        else:
            shelf.run('mkdir', '-p', dest_dir)
            if os.path.isdir(os.path.join(source.dir, '.hg')):
                shelf.run('hg', 'clone', source.dir, dest_dir)
            elif os.path.isdir(os.path.join(source.dir, '.git')):
                shelf.run('git', 'clone', source.dir, dest_dir)
            else:
                raise NotImplementedError('source "%s" is not version-controlled' %
                                          source.name)
