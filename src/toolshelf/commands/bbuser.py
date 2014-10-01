"""
    ghuser [--login <login>] <username>
        Create (on standard output) a catalog for all of the given Github user's
        repositories.  If the --login option is given, the Github API will be
        logged into using the login username (not necessarily the same as the
        target username).  A password will be prompted for the login username.
        If --login is not given, the Github API will be used anonymously, with
        all the caveats that implies.  Note that this command is experimental.

    bbuser --login <login> <username>
        Like ghuser, but for the Bitbucket API.  The --login option is required
        and the login username must be the same as the target username.  (This
        appears to be a limitation of the Bitbucket API.)  Note that this
        command is experimental.
"""

import getpass

# pip install --user bitbucket-api
from bitbucket.bitbucket import Bitbucket

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def process_args(self, shelf, args):
        # this only works for the logged-in user.  It would be great if...
        # yeah.
        username = args[0]
        assert shelf.options.login is not None, \
            '--login must be supplied when accessing the Bitbucket API'
        password = getpass.getpass('Password: ')
        bb = Bitbucket(username, password)
        success, repositories = bb.repository.all()
        for repo in sorted(repositories):
            print 'bb:%s/%s' % (username, repo['slug'])
        return []
