"""
ghuser [--login <login>] <username>

Create (on standard output) a catalog for all of the given Github user's
repositories.  If the --login option is given, the Github API will be
logged into using the login username (not necessarily the same as the
target username).  A password will be prompted for the login username.
If --login is not given, the Github API will be used anonymously, with
all the caveats that implies.  Note that this command is experimental.
"""

import getpass
import os
import re

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def process_args(self, shelf, args):
        import requests

        user = args[0]
        auth = None
        if shelf.options.login is not None:
            password = getpass.getpass('Password: ')
            auth = (shelf.options.login, password)
        url = 'https://api.github.com/users/%s/repos' % user
        
        done = False
        while not done:
            response = requests.get(url, auth=auth)
            data = response.json()
            if 'message' in data:
                raise ValueError(data)
            for x in data:
                print 'gh:%s' % x['full_name']
            link = response.headers.get('Link', None)
            if link is None:
                done = True
            else:
                match = re.match(r'\<(.*?)\>\s*\;\s*rel\s*=\s*\"next\"', link)
                if not match:
                    shelf.note(link)
                    done = True
                else:
                    url = match.group(1)
