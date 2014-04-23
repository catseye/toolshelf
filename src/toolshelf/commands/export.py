import os
import subprocess
import sys

def export(shelf, args):
    def export_it(source):
        dest_dir = os.path.join(shelf.options.output_dir, source.name)
        shelf.run('mkdir', '-p', dest_dir)
        if os.path.isdir(os.path.join(source.dir, '.hg')):
            shelf.run('hg', 'clone', source.dir, dest_dir)
        elif os.path.isdir(os.path.join(source.dir, '.git')):
            shelf.run('git', 'clone', source.dir, dest_dir)
        else:
            raise NotImplementedError('source "%s" is not version-controlled' %
                                      source.name)

    shelf.foreach_specced_source(
        shelf.expand_docked_specs(args), export_it
    )
