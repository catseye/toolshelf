import re

import requests

def ghuser(shelf, args):
    login = args[0]
    user = args[1]
    if login == 'none':
        login = ''
    else:
        login = login + '@'
    url = 'https://%sapi.github.com/users/%s/repos' % (login, user)
    
    done = False
    while not done:
        response = requests.get(url)
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
