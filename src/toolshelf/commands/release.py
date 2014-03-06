import os
import re

def release(shelf, args):
    """Create a distfile from the latest tag in a local version-controlled
    source tree.
    
    """
    sources = shelf.make_sources_from_specs(
        shelf.expand_docked_specs(args)
    )
    for source in sources:
        # wouldn't need this if we used foreach_specced_sources
        shelf.chdir(source.dir)
        distro = source.project
        tag = source.get_latest_release_tag()
        if not tag:
            raise SystemError("Repository not tagged")
        diff = shelf.get_it('hg diff -r %s -r tip -X .hgtags' % tag)
        if diff and not shelf.options.force:
            raise SystemError("There are changes to mainline since latest tag")

        match = re.match(r'^rel_(\d+)_(\d+)_(\d+)_(\d+)$', tag)
        if match:
            v_maj = match.group(1)
            v_min = match.group(2)
            r_maj = match.group(3)
            r_min = match.group(4)
            filename = '%s-%s.%s-%s.%s.zip' % (
                distro, v_maj, v_min, r_maj, r_min
            )
        else:
            match = re.match(r'^rel_(\d+)_(\d+)$', tag)
            if match:
                v_maj = match.group(1)
                v_min = match.group(2)
                r_maj = "0"
                r_min = "0"
                filename = '%s-%s.%s.zip' % (distro, v_maj, v_min)
            else:
                raise ValueError("Not a release tag that I understand: %s" % tag)
        print """\
  - version: "%s.%s"
    revision: "%s.%s"
    url: http://catseye.tc/distfiles/%s
""" % (v_maj, v_min, r_maj, r_min, filename)
        full_filename = os.path.join(shelf.options.distfiles_dir, filename)
        if os.path.exists(full_filename):
            shelf.run('unzip', '-v', full_filename)
            raise SystemError("Distfile already exists: %s" % full_filename)
        command = ['hg', 'archive', '-t', 'zip', '-r', tag]
        for x in ('.hgignore', '.gitignore',
                  '.hgtags', '.hg_archival.txt'):
            command.append('-X')
            command.append(x)
        command.append(full_filename)
        shelf.run(*command)
        shelf.run('unzip', '-v', full_filename)
