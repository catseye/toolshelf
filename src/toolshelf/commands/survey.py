"""
Generate report summarizing various properties of the specified sources.

Sort of a "deep status".

"""

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def setup(self, shelf):
        self.repos = {}

    def perform(self, shelf, source):
        print source.name
        dirty = shelf.get_it("hg st")
        tags = {}
        latest_tag = source.get_latest_release_tag(tags)
        due = ''
        diff = ''
        if latest_tag is None:
            due = 'NEVER RELEASED'
        else:
            diff = shelf.get_it('hg diff -r %s -r tip -X .hgtags' % latest_tag)
            if not diff:
                due = ''
            else:
                due = "%d changesets (tip=%d, %s=%d)" % \
                    ((tags['tip'] - tags[latest_tag]), tags['tip'],
                     latest_tag, tags[latest_tag])
        self.repos[source.name] = {
            'dirty': dirty,
            'outgoing': '',
            'tags': tags,
            'latest_tag': latest_tag,
            'due': due,
            'diff': diff,
        }

    def teardown(self, shelf):
        repos = self.repos
        print '-----'
        for repo in sorted(repos.keys()):
            r = repos[repo]
            if r['dirty'] or r['outgoing'] or r['due']:
                print repo
                if r['dirty']:
                    print r['dirty']
                if r['outgoing']:
                    print r['outgoing']
                if r['due']:
                    print "  DUE:", r['due']
                print
        print '-----'
