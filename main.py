import time

from mwcleric import AuthCredentials
from mwcleric import WikiggClient
from mwclient import AssertUserFailedError
from mwclient.page import Page


class Loadout:
    startat_namespace = 0
    startat_page = None
    # noinspection PyRedeclaration
    # startat_page = 'Module:Navbox/Aether II/en'  # uncomment & edit this line if you want to resume running in the middle
    overwrite_existing = True
    summary = 'Adding default set of pages'

    def __init__(self):
        self.passed_startat = False
        credentials = AuthCredentials(user_file="me", use_site_pw=False)  # set to True iff the wiki is onboarding
        self.loadout = WikiggClient('defaultloadout')
        self.target = WikiggClient('gg', credentials=credentials)  # edit the wiki here

    def run(self):
        self.copy()
        self.move()

    def copy(self):
        for ns in self.loadout.client.namespaces:
            print(f"Starting namespace {ns}")
            if ns > self.startat_namespace - 1:  # ns 4 is Project ns
                for orig_page in self.loadout.client.allpages(namespace=ns):
                    orig_page: Page
                    time.sleep(1)
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
                            protections = '|'.join([f'{k}={v[0]}' for k, v in orig_page.protection.items()])
                            self.target.protect(target_page, protections=protections)

                        except AssertUserFailedError:
                            self.target.login()
                            target_page.save(orig_page.text(), summary=self.summary)

    def move(self):
        loadout_mainpage = self.loadout.client.site['mainpage']
        target_mainpage = self.target.client.site['mainpage']
        self.target.client.pages[loadout_mainpage].move(target_mainpage, reason="Move main page for new wiki",
                                                        no_redirect=True)


if __name__ == '__main__':
    Loadout().run()
