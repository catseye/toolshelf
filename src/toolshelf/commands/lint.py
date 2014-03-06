import os

def lint(shelf, args):
    """Check that the layouts of distributions conform to some
    distribution organization guidelines.  If these are not guidelines that
    you use, you can take this with a grain of salt.

    """
    problems = {}

    OK_ROOT_FILES = (
        'LICENSE', 'UNLICENSE',
        'README.markdown', 'TODO.markdown', 'HISTORY.markdown',
        'test.sh', 'clean.sh',
        'make.sh', 'make-cygwin.sh', 'Makefile',
        '.hgtags', '.hgignore', '.gitignore',
    )
    OK_ROOT_DIRS = (
        'bin', 'contrib', 'demo', 'dialect',
        'disk', 'doc', 'ebin', 'eg', 'images',
        'impl', 'lib', 'priv', 'script',
        'src', 'tests',
        '.hg',
    )

    def lint_it(source):
        prob = []
        if not os.path.exists('README.markdown'):
            prob.append("No README.markdown")
        if not os.path.exists('LICENSE') and not os.path.exists('UNLICENSE'):
            prob.append("No LICENSE or UNLICENSE")
        if os.path.exists('LICENSE') and os.path.exists('UNLICENSE'):
            prob.append("Both LICENSE and UNLICENSE")
        for root, dirnames, filenames in os.walk('.'):
            if root.endswith(".hg"):
                del dirnames[:]
                continue
            if root == '.':
                root_files = []
                for filename in filenames:
                    if filename not in OK_ROOT_FILES:
                        root_files.append(filename)
                if root_files:
                    prob.append(
                        "Junk files in root: %s" % root_files
                    )

                root_dirs = []
                for dirname in dirnames:
                    if dirname not in OK_ROOT_DIRS:
                        root_dirs.append(dirname)
                if root_dirs:
                    prob.append(
                        "Junk dirs in root: %s" % root_dirs
                    )
        problems[source.dir] = prob

    shelf.foreach_specced_source(
        shelf.expand_docked_specs(args), lint_it
    )

    problematic_count = 0
    for d in sorted(problems.keys()):
        if not problems[d]:
            continue
        print d
        print '-' * len(d)
        print
        for problem in problems[d]:
            print "* %s" % problem
        print
        problematic_count += 1

    #print "Linted %d clones, problems in %d of them." % (
    #    count, problematic_count
    #)
