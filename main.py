import time

import requests.exceptions
from mwcleric import AuthCredentials
from mwcleric import WikiggClient
from mwcleric.models.simple_page import SimplePage
from mwclient import AssertUserFailedError, APIError
from mwclient.page import Page


class Loadout:
    target_name = 'gg'
    startat_namespace = 0
    startat_page = None
    # noinspection PyRedeclaration
    # startat_page = 'MediaWiki:Vector.css'  # uncomment & edit this line if you want to resume running in the middle

    overwrite_existing = True
    summary = 'Adding default set of pages'

    def __init__(self):
        self.passed_startat = False
        credentials = AuthCredentials(user_file="me", use_site_pw=True)  # set to True iff the wiki is onboarding
        self.loadout = WikiggClient('defaultloadout')
        self.target = WikiggClient(self.target_name, credentials=credentials)  # edit the wiki here

    def run(self):
        self.copy()
        self.move()

    def copy(self):
        for ns in self.loadout.client.namespaces:
            print(f"Starting namespace {ns}")
            if ns <= self.startat_namespace - 1:  # ns 4 is Project ns
                continue
            if ns == 0:
                continue
            self.copy_namespace(ns)
        self.copy_namespace(0)

    def copy_namespace(self, ns: int):
        for orig_page in self.loadout.client.allpages(namespace=ns):
            try:
                self.copy_page(orig_page, ns)
            except requests.exceptions.HTTPError:
                time.sleep(60)
                self.copy_page(orig_page, ns)

    def copy_page(self, orig_page: Page, ns: int):
        if self.startat_page == orig_page.name:
            self.passed_startat = True
        if self.startat_page is not None and not self.passed_startat:
            return
        print(orig_page.name)
        new_title = orig_page.name
        if ns == 4:
            new_title = f'Project:{orig_page.page_title}'
        target_page = self.target.client.pages[new_title]
        if self.overwrite_existing or not target_page.exists:
            self.save(target_page, orig_page)

    def save(self, target_page: Page, orig_page: Page):
        self.target.save(target_page, text=orig_page.text(), summary=self.summary)
        protections = '|'.join([f'{k}={v[0]}' for k, v in orig_page.protection.items()])
        if protections != '':
            self.target.protect(target_page, protections=protections)

    def move(self):
        # TODO: handle this immediately when creating the pages
        if self.overwrite_existing is False:
            return
        loadout_mainpage_name = self.loadout.client.site['mainpage']
        target_mainpage_name = self.target.client.site['mainpage']
        if target_mainpage_name == 'Main Page':
            # support not overwriting the main page message if it was previously existing
            # but if it was "Main Page" then force the new location because siteinfo is cached
            # TODO: force cache update here
            target_mainpage_name = self.target.client.site['sitename']

        target_mainpage = self.target.client.pages[loadout_mainpage_name]
        self.target.move(target_mainpage, target_mainpage_name, reason="Move main page for new wiki",
                         no_redirect=True, ignore_warnings=True)
        if target_mainpage_name != "Main Page":
            self.target.client.pages['Main Page'].save(f'#redirect [[{target_mainpage_name}]]')


if __name__ == '__main__':
    Loadout().run()
