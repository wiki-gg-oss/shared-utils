import time

import requests.exceptions
from mwcleric import AuthCredentials
from mwcleric import WikiggClient
from mwclient.page import Page

WIKIS = ['gg']


class Loadout:
    startat_namespace = 0
    startat_page = None
    # noinspection PyRedeclaration
    # startat_page = 'Template:License'
    is_import = False  # don't overwrite & don't make mainspace pages
    skip_css = False
    summary = 'Adding default set of pages'

    def __init__(self, target_name):
        self.passed_startat = False
        credentials = AuthCredentials(user_file="me")  # set to True iff the wiki is onboarding
        self.target_name = target_name
        self.loadout = WikiggClient('defaultloadout')
        self.target = WikiggClient(target_name, credentials=credentials)  # edit the wiki here

    def run(self):
        self.copy()

    def copy(self):
        for ns in self.loadout.client.namespaces:
            print(f"Starting namespace {ns}")
            if ns <= self.startat_namespace - 1:  # ns 4 is Project ns
                continue
            if ns == 0:
                continue
            self.copy_namespace(ns)
        if not self.is_import:
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
        if orig_page.name == 'File:Site-favicon.ico':
            # don't copy the favicon page, to avoid warnings when people upload it
            return
        print(orig_page.name)
        new_title = orig_page.name
        new_site_name = self.target.client.site['sitename']
        if ns == 4:
            new_title = f'Project:{orig_page.page_title}'
        if orig_page.name == self.loadout.client.site['mainpage']:
            new_title = new_site_name
        if orig_page.name == 'Category:' + self.loadout.client.site['sitename']:
            new_title = 'Category:' + new_site_name
        target_page = self.target.client.pages[new_title]
        do_save = False
        if not self.is_import:
            # if it's not an import we always do the save
            # except at page MediaWiki copyright, then we don't want to overwrite
            if new_title != 'MediaWiki:Copyright':
                do_save = True
        elif new_title in ['MediaWiki:Common.css', 'MediaWiki:Vector.css']:
            if not self.skip_css:
                do_save = True
        elif not target_page.exists and new_title != 'MediaWiki:Copyright':
            do_save = True
        if do_save:
            self.save(target_page, orig_page)

    def save(self, target_page: Page, orig_page: Page):
        text = orig_page.text()
        if target_page.name == 'Main Page':
            target_mainpage_name = self.target.client.site['sitename']
            text = f'#redirect [[{target_mainpage_name}]]'
        self.target.save(target_page, text, summary=self.summary)
        protections = '|'.join([f'{k}={v[0]}' for k, v in orig_page.protection.items()])
        if protections != '':
            self.target.protect(target_page, protections=protections)


if __name__ == '__main__':
    for wiki in WIKIS:
        Loadout(wiki).run()
