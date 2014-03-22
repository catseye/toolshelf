import re

import getpass
import optparse
import requests

def ghuser(shelf, args):
    user = args[0]
    auth = None
    if shelf.options.login is not None:
        password = getpass.getpass('Password: ')
        auth = (shelf.options.login, password)
    url = 'https://api.github.com/users/%s/repos' % user
    
    done = False
    while not done:
        response = requests.get(url, auth=auth)
        #for header in ('X-RateLimit-Limit', 'X-RateLimit-Remaining'):
        #    print header, response.headers[header]
        data = response.json()
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

def bbuser(shelf, args):
    # this only works for the logged-in user.  It would be great if...
    # yeah.
    from bitbucket.bitbucket import Bitbucket
    (username, password) = args[0].split(':')
    bb = Bitbucket(username, password)
    success, repositories = bb.repository.all()
    for repo in sorted(repositories):
        print 'bb:%s/%s' % (username, repo['slug'])
