# Prepare IMProved Main Page
# (import just IMP stuff)
import time,re

import requests.exceptions
from mwcleric import AuthCredentials
from mwcleric import WikiggClient
from mwclient.page import Page

WIKIS = ['gg:en']


class Loadout:
    summary = 'Adding IMP pages'

    categories = ['Main page templates', 'Main page boxes']
    additional_pages = ['Module:Main_page', 'MediaWiki:Gadget-mpEditLinks', 'MediaWiki:Gadget-mpEditLinks.js', 'MediaWiki:Gadget-mpEditLinks.css']

    appending_pages = {
        'MediaWiki:Gadgets-definition' : '\n* mpEditLinks[ResourceLoader|rights=editprotected|default]|mpEditLinks.css|mpEditLinks.js',
    }

    def __init__(self, target_name, target_lang):
        credentials = AuthCredentials(user_file="me")  # set to True iff the wiki is onboarding
        self.target_name = target_name
        self.target_lang = target_lang
        self.loadout = WikiggClient('defaultloadout')
        self.target = WikiggClient(target_name, credentials=credentials, lang=target_lang)  # edit the wiki here

    def run(self):
        self.copy()

    def copy(self):
        # copy the categories and their members
        for cat in self.categories:
            print(f"Starting category {cat}")
            self.copy_category(cat)

        # copy the individual pages
        print("Starting individual pages")
        for page in self.additional_pages:
            self.copy_page(self.loadout.client.pages[page])

        # append text to pages that have appending text set
        print("Starting appending pages")
        for page, text in self.appending_pages.items():
            self.append(self.loadout.client.pages[page], text)

        # copy the main page itself
        print("Copying main page")
        self.copy_page(self.loadout.client.pages[self.loadout.client.site['mainpage']])
        

    def copy_category(self, cat: str):
        for orig_page in self.loadout.client.categories[cat]:
            try:
                self.copy_page(orig_page)
            except requests.exceptions.HTTPError:
                time.sleep(60)
                self.copy_page(orig_page)

            # copy the doc if it exists
            doc = self.loadout.client.pages[orig_page.name + '/doc']
            if doc.exists:
                self.copy_page(doc)

        # copy the category page itself
        self.copy_page(self.loadout.client.categories[cat])

    def copy_mp_css(self):
        text = '\n\n' + re.search(r'(^\/\*+\n\* Main page layout \*.+End main page layout \*\n\*+\/)', self.loadout.client.pages['MediaWiki:Common.css'].text(), flags=re.DOTALL | re.MULTILINE).group(0)
        self.append(self.target.client.pages['MediaWiki:Common.css'], text)

    def copy_page(self, orig_page: Page):
        print(orig_page.name)
        new_title = orig_page.name

        # Put the main page under the correct local name
        if orig_page.base_name == self.loadout.client.site['mainpage']:
            new_title = orig_page.name.replace(self.loadout.client.site['mainpage'], self.target.client.site['mainpage'])

        target_page = self.target.client.pages[new_title]
        self.save(target_page, orig_page)

    def save(self, target_page: Page, orig_page: Page):
        text = orig_page.text()

        self.target.save(target_page, text, summary=self.summary)

    def append(self, target_page: Page, text: str):
        print(target_page.name)
        self.target.append(target_page, text, summary=self.summary)


if __name__ == '__main__':
    for wiki in WIKIS:
        if ':' in wiki:
            name, lang = wiki.split(':')
            Loadout(name, lang).run()
        else:
            Loadout(wiki, None).run()
