import time

from mwcleric.errors import RetriedLoginAndStillFailed
from mwcleric.wikigg_client import WikiggClient
from mwcleric.auth_credentials import AuthCredentials
from mwclient import APIError

credentials = AuthCredentials(user_file="bot")

wikis = ['gg']

for wiki in wikis:
    limit = -1
    startat_page = None
    # startat_page = 'Zuchtzentrum'
    site = WikiggClient(wiki, credentials=credentials)  # Set wiki
    # this_template = site.client.pages['Template:Infobox Player']  # Set template
    # pages = this_template.embeddedin()

    # pages = site.client.categories['Pages with script errors']

    pages = site.client.allpages(namespace=3)

    passed_startat = False if startat_page else True
    lmt = 0
    for page in pages:
        if lmt == limit:
            break
        if startat_page and page.name == startat_page:
            passed_startat = True
        if not passed_startat:
            continue
        print('Deleting page %s...' % page.name)
        try:
            site.delete(page)
        except APIError:
            continue
        except RetriedLoginAndStillFailed:
            continue
