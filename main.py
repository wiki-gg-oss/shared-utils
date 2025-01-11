import argparse
import time

import requests.exceptions
from mwcleric import AuthCredentials
from mwcleric import WikiggClient
from mwclient.page import Page


WIKIS = ['gg:en']
IS_IMPORT = False  # don't overwrite (except the main page)
SKIP_CSS = False
START_AT_PAGE = None
START_AT_NAMESPACE = 0
SUBJECT_NAME = None


class Loadout:
    startat_namespace = 0
    startat_page = None
    # noinspection PyRedeclaration
    # startat_page = 'Template:License'
    is_import: bool
    skip_css: bool
    summary: str = 'Adding default set of pages'
    subject_name: str = None
    docpage: str = '/doc'

    def __init__(self,
                 target_name,
                 target_lang,
                 is_import,
                 skip_css,
                 start_at_page,
                 start_at_ns,
                 subject_name):
        self.passed_startat = False
        credentials = AuthCredentials(user_file="me")
        self.target_name = target_name
        self.target_lang = target_lang
        self.is_import = is_import
        self.skip_css = skip_css
        self.startat_page = start_at_page
        self.startat_namespace = start_at_ns
        self.loadout = WikiggClient('defaultloadout')
        self.target = WikiggClient(target_name, credentials=credentials, lang=target_lang)

        self.orig_main_page_name = self.loadout.client.site['mainpage']
        self.target_main_page_name = self.target.client.site['sitename']

        self.subject_name = subject_name
        if subject_name is None:
            sitename: str = self.target.client.site['sitename']
            if sitename.endswith(' Wiki'):
                self.subject_name = sitename.removesuffix(' Wiki')

        self.docpage = '/doc'
        if target_lang is not None and target_lang != 'en':
            doc_page_name = self.target.localize('Scribunto-doc-page-name')
            print(doc_page_name)
            page, docpage = doc_page_name.split('/')
            self.docpage = '/' + docpage
        

    def run(self):
        self.copy()

    def copy(self):
        for ns in self.loadout.client.namespaces:
            if ns <= self.startat_namespace - 1:
                continue

            self.copy_namespace(ns)
        
        # note for future reference:
        # Even after the mediawiki namespace is processed, self.target.client.site['sitename'] does not update.
        # I believe this is because that value is only fetched once when the client object is first initialized

        if self.is_import:
            self.redirect_mainpage()
            self.add_user_migration_notes()

    def copy_namespace(self, ns: int):
        print(f"Starting namespace {ns}")
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
        print(f'Processing {orig_page.name}')
        new_title = orig_page.name
        if ns == 4: # ns 4 is Project ns
            new_title = f'Project:{orig_page.page_title}'
        if orig_page.base_name == self.orig_main_page_name: # if we're on the dlw main page, change the name to the local wiki's main page name
            new_title = orig_page.name.replace(self.orig_main_page_name, self.target_main_page_name) # the replace is for handling subpages
        if orig_page.name == 'Category:' + self.orig_main_page_name: # if we're on the dlw root category, change the name to the local wiki's name
            new_title = 'Category:' + self.target_main_page_name
        if orig_page.namespace == 828 and orig_page.name.endswith('/doc'): # for doc pages, replace /doc with the localized equivalent
            new_title = new_title.replace('/doc', self.docpage)

        target_page = self.target.client.pages[new_title]
        do_save = False

        if self.is_import:
            if new_title == 'MediaWiki:Copyright': # skip Mediawiki:Copyright
                pass
            elif new_title in ['MediaWiki:Common.css', 'MediaWiki:Vector.css']: #if skip_css is true, skip these pages
                if not self.skip_css:
                    do_save = True
            elif target_page.exists: # if the target page already exists, only overwrite if it's the main page
                if new_title == self.target_main_page_name:
                    do_save = True
            else: # save in all other cases
                do_save = True
        else:
            # if it's not an import we always do the save
            # except at page MediaWiki copyright, then we don't want to overwrite
            if new_title != 'MediaWiki:Copyright' or not target_page.exists:
                do_save = True
                
        if do_save:
            self.save(target_page, orig_page)

    def save(self, target_page: Page, orig_page: Page):
        text = orig_page.text()
        if self.subject_name is not None:
            text = text.replace('SUBJECTNAME', self.subject_name)
        if target_page.name == 'Main Page':
            target_mainpage_name = self.target.client.site['sitename']
            text = f'#redirect [[{target_mainpage_name}]]'
        self.target.save(target_page, text, summary=self.summary)
        protections = '|'.join([f'{k}={v[0]}' for k, v in orig_page.protection.items()])
        if protections != '':
            try:
                self.target.protect(target_page, protections=protections)
            except Exception as e:
                pass

    def redirect_mainpage(self):
        mainpage = self.target.client.pages['Main Page']
        if 'MediaWiki has been installed' in mainpage.text():
            target_mainpage_name = self.target.client.site['sitename']
            text = f'#redirect [[{target_mainpage_name}]]'
            self.target.save(mainpage, text)

    def add_user_migration_notes(self):
        text = '{{int:wikigg-fork-reclaim-note}}'
        for page_title in ('MediaWiki:Loginprompt', 'MediaWiki:Signupstart'):
            page = Page(self.target.client, page_title)
            self.target.save(page, text, summary=self.summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--is-import', action='store_true', default=IS_IMPORT)
    parser.add_argument('-s', '--skip-css', action='store_true', default=SKIP_CSS)
    parser.add_argument('-p', '--from-page', type=str, default=START_AT_PAGE)
    parser.add_argument('-n', '--from-namespace', type=int, default=START_AT_NAMESPACE)
    parser.add_argument('wikis', nargs='*', default=WIKIS)
    args = parser.parse_args()

    common_bot_args = dict(
        is_import=args.is_import,
        skip_css=args.skip_css,
        start_at_page=args.from_page,
        start_at_ns=args.from_namespace,
    )

    if args.is_import:
        print("This is an import wiki, pages other than the mainpage will not be overwritten.")
    if args.skip_css:
        print("CSS pages will be skipped.")

    for wiki in args.wikis:
        name, lang = wiki, None
        if ':' in wiki:
            name, lang = wiki.split(':')
        Loadout(name, lang, subject_name=SUBJECT_NAME, **common_bot_args).run()
