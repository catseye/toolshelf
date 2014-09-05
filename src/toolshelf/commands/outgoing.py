def outgoing(shelf, args):
    """Reports which docked source trees have changes that are not in the
    upstream repo.  Quite crude.

    """
    def outgoing_it(source):
        print source.name
        shelf.run('hg', 'out')
        #outgoing = shelf.get_it("hg out")
        #if 'no changes found' not in outgoing:
        #    print outgoing

    shelf.foreach_specced_source(
        shelf.expand_docked_specs(args), outgoing_it
    )
