import time

from mwcleric import AuthCredentials
from mwcleric import WikiggClient
from mwclient import AssertUserFailedError


class Loadout:
    startat_namespace = 0
    startat_page = None
    # noinspection PyRedeclaration
    # startat_page = 'Module:Navbox/Aether II/en'  # uncomment & edit this line if you want to resume running in the middle
    overwrite_existing = True
    summary = 'Adding default set of pages'

    def __init__(self):
        self.passed_startat = False
        credentials = AuthCredentials(user_file="me", use_site_pw=True)
        self.loadout = WikiggClient('defaultloadout')
        self.target = WikiggClient('rl-esports', credentials=credentials)  # edit the wiki here

    def run(self):
        pass

    def copy(self):
        for ns in self.loadout.client.namespaces:
            print(f"Starting namespace {ns}")
            if ns > self.startat_namespace - 1:  # ns 4 is Project ns
                for orig_page in self.loadout.client.allpages(namespace=ns):
                    time.sleep(0.5)
                    print(orig_page.name)
                    new_title = orig_page.name
                    if ns == 4:
                        new_title = 'Project:{}'.format(orig_page.page_title)
                    if self.startat_page == orig_page.name:
                        self.passed_startat = True
                    if self.startat_page and not self.passed_startat:
                        continue
                    target_page = self.target.client.pages[new_title]
                    if self.overwrite_existing or not target_page.exists:
                        try:
                            target_page.save(orig_page.text(), summary=self.summary)
                            for k, v in orig_page.protection.items():
                                self.target.client.api('protect',
                                                       title=target_page.name,

                                                       expiry=v[1],
                                                       reason="Copying protection level from loadout"
                                                       )


                        except AssertUserFailedError:
                            self.target.login()
                            target_page.save(orig_page.text(), summary=self.summary)

    def move(self):
        loadout_mainpage = self.loadout.client.site['mainpage']
        target_mainpage = self.target.client.site['mainpage']
        self.target.client.pages[loadout_mainpage].move(target_mainpage, reason="Move main page for new wiki",
                                                        no_redirect=True)
