from toolshelf.toolshelf import expand_docked_specs, get_it

def survey(self, args):
    """Generates a report summarizing various properties of the docked
    source trees.  Sort of a "deep status".

    """
    repos = {}

    def survey_it(source):
        print source.name
        dirty = get_it("hg st")
        outgoing = ''
        #if hg_outgoing:
        #    outgoing = get_it("hg out")
        #if 'no changes found' in outgoing:
        #    outgoing = ''
        tags = {}
        latest_tag = source.get_latest_release_tag(tags)
        due = ''
        diff = ''
        if latest_tag is None:
            due = 'NEVER RELEASED'
        else:
            diff = get_it('hg diff -r %s -r tip -X .hgtags' % latest_tag)
            if not diff:
                due = ''
            else:
                due = "%d changesets (tip=%d, %s=%d)" % \
                    ((tags['tip'] - tags[latest_tag]), tags['tip'],
                     latest_tag, tags[latest_tag])
        repos[source.name] = {
            'dirty': dirty,
            'outgoing': outgoing,
            'tags': tags,
            'latest_tag': latest_tag,
            'due': due,
            'diff': diff,
        }

    self.foreach_source(
        expand_docked_specs(args), survey_it,
        rebuild_paths=False
    )

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
