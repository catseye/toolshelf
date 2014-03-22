import re

import getpass
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
