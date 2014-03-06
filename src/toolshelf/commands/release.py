import os
import re

from toolshelf.toolshelf import expand_docked_specs, get_it, run

def release(self, args):
    """Create a distfile from the latest tag in a local version-controlled
    source tree.
    
    """
    cwd = os.getcwd()
    specs = expand_docked_specs(args, default_all=False)
    sources = self.make_sources_from_specs(specs)
    for source in sources:
        distro = source.project
        tag = source.get_latest_release_tag()
        if not tag:
            raise SystemError("Repository not tagged")
        os.chdir(source.dir)
        diff = get_it('hg diff -r %s -r tip -X .hgtags' % tag)
        if diff and not self.options.force:
            raise SystemError("There are changes to mainline since latest tag")
        os.chdir(cwd)

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
        full_filename = os.path.join(self.options.distfiles_dir, filename)
        if os.path.exists(full_filename):
            run('unzip', '-v', full_filename)
            raise SystemError("Distfile already exists: %s" % full_filename)
        command = ['hg', 'archive', '-t', 'zip', '-r', tag]
        for x in ('.hgignore', '.gitignore',
                  '.hgtags', '.hg_archival.txt'):
            command.append('-X')
            command.append(x)
        command.append(full_filename)
        os.chdir(source.dir)
        run(*command)
        os.chdir(cwd)
        run('unzip', '-v', full_filename)
