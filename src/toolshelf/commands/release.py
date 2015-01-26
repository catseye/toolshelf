"""
Create a release distfile from the latest tag in a docked source.
"""

import os
import re

from toolshelf.toolshelf import BaseCommand

def match_tag(distro, tag):
    match = re.match(r'^rel_(\d+)_(\d+)_(\d+)_(\d+)$', tag)
    if match:
        v_maj = match.group(1)
        v_min = match.group(2)
        r_maj = match.group(3)
        r_min = match.group(4)
        filename = '%s-%s.%s-%s.%s.zip' % (
            distro, v_maj, v_min, r_maj, r_min
        )
        return (v_maj, v_min, r_maj, r_min, filename)

    match = re.match(r'^rel_(\d+)_(\d+)$', tag)
    if match:
        v_maj = match.group(1)
        v_min = match.group(2)
        filename = '%s-%s.%s.zip' % (distro, v_maj, v_min)
        return (v_maj, v_min, "0", "0", filename)

    match = re.match(r'^v?(\d+)\.(\d+)\-(\d+)\.(\d+)$', tag)
    if match:
        v_maj = match.group(1)
        v_min = match.group(2)
        r_maj = match.group(3)
        r_min = match.group(4)
        filename = '%s-%s.%s-%s.%s.zip' % (
            distro, v_maj, v_min, r_maj, r_min
        )
        return (v_maj, v_min, r_maj, r_min, filename)

    match = re.match(r'^v?(\d+)\.(\d+)$', tag)
    if match:
        v_maj = match.group(1)
        v_min = match.group(2)
        filename = '%s-%s.%s.zip' % (distro, v_maj, v_min)
        return (v_maj, v_min, "0", "0", filename)

    raise ValueError("Not a release tag that I understand: %s" % tag)


class Command(BaseCommand):
    """Create a distfile from the latest tag in a local version-controlled
    source tree.

    """
    def perform(self, shelf, source):
        tag = source.tag
        if not tag:
            tag = source.get_latest_release_tag()
        if not tag:
            raise SystemError("Repository not tagged")
        (v_maj, v_min, r_maj, r_min, filename) = match_tag(source.project, tag)
        full_filename = os.path.join(shelf.options.output_dir, filename)
        if os.path.exists(full_filename):
            shelf.run('unzip', '-v', full_filename)
            raise SystemError("Distfile already exists: %s" % full_filename)
        command = ['hg', 'archive', '-t', 'zip', '-r', tag]
        for x in ('.hgignore', '.gitignore',
                  '.hgtags', '.hg_archival.txt'):
            command.append('-X')
            command.append(x)
        # hg archive -t zip -r 1.0 -X .hgignore -X .gitignore -X .hgtags -X .hg_archival.txt foobar-1.0.zip
        command.append(full_filename)
        shelf.run(*command)
        shelf.run('unzip', '-v', full_filename)
        # Chrysoberyl entry
        print """\
  - version: "%s.%s"
    revision: "%s.%s"
    url: http://catseye.tc/distfiles/%s
""" % (v_maj, v_min, r_maj, r_min, filename)
