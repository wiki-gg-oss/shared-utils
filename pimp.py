# Prepare IMProved Main Page
# (import just IMP stuff)
# add the -u arg to only update (don't overwrite box pages)
import time, re, argparse

import requests.exceptions
from mwcleric import AuthCredentials
from mwcleric import WikiggClient
from mwclient.page import Page

WIKIS = ['gg:en']
UPDATE_ONLY = False # If true: don't copy the content boxes, don't append gadget definition
IS_IMPORT = False # If true: only copy the content boxes. This is for use on imported wikis, where DLW is copied except for mainspace


class Loadout:

    categories = ['Main page templates', 'Main page boxes']
    additional_pages = ['Module:Main_page', 'MediaWiki:Gadgets/mpEditLinks', 'MediaWiki:Gadgets/mpEditLinks/main.js', 'MediaWiki:Gadgets/mpEditLinks/main.css', 'MediaWiki:Gadgets/imp', 'MediaWiki:Gadgets/imp/variablesEditMe.css', 'MediaWiki:Gadgets/imp/mainReadonly.css', 'MediaWiki:Gadgets/imp/customEditMe.css', 'Category:Pages using IMP'] #Category:Pages using IMP is here instead of in categories because we only want the category page itself, not its members

    def __init__(self, target_name, target_lang, update_only, is_import):
        credentials = AuthCredentials(user_file="me")
        self.target_name = target_name
        self.target_lang = target_lang
        self.loadout = WikiggClient('defaultloadout')
        self.target = WikiggClient(target_name, credentials=credentials, lang=target_lang)
        self.update_only = update_only
        self.is_import = is_import

        self.orig_main_page = self.loadout.client.pages[self.loadout.client.site['mainpage']]
        self.target_main_page = self.target.client.pages[self.target.client.site['mainpage']]

        self.summary = 'Adding IMP pages'

    def run(self):

        if self.update_only:
            self.summary = "Updating IMP pages"
            self.copy_update()
        elif self.is_import:
            self.summary = "Adding IMP boxes"
            self.copy_import()
        else:
            self.copy_all()

        # run these under all options
        self.move()
        self.purge_main_page()

    def copy_update(self):
        self.copy_pages()
        self.copy_category('Main page templates')

    def copy_import(self):
        self.copy_category('Main page boxes')

    def copy_all(self):
        # copy the categories and their members
        self.copy_categories()

        # copy the individual pages
        self.copy_pages()

        # append the CSS to common.css
        self.copy_mp_css()

        # copy the main page itself
        self.copy_page(self.orig_main_page)

    def copy_categories(self):
        for cat in self.categories:
            if self.update_only and cat == 'Main page boxes':
                continue
            print(f"Starting category {cat}")
            self.copy_category(cat)

    def copy_category(self, cat: str):
        for orig_page in self.loadout.client.categories[cat]:
            self.copy_page(orig_page)

        # copy the category page itself
        self.copy_page(self.loadout.client.categories[cat])

    def copy_mp_css(self):
        text = '\n\n' + re.search(r'(^\/\*+\n\* \[\[Template:MP link\]\] \*.+End Template:MP link \*\n\*+\/)', self.loadout.client.pages['MediaWiki:Common.css'].text(), flags=re.DOTALL | re.MULTILINE).group(0)
        self.append(self.target.client.pages['MediaWiki:Common.css'], text)

    def copy_pages(self):
        print("Starting individual pages")
        for page in self.additional_pages:
            self.copy_page(self.loadout.client.pages[page])

    def copy_page(self, orig_page: Page):
        print(f"Processing {orig_page.name}")
        new_title = orig_page.name

        # Put the main page under the correct local name
        if orig_page.base_name == self.orig_main_page.name:
            new_title = orig_page.name.replace(self.orig_main_page.name, self.target_main_page.name)

        target_page = self.target.client.pages[new_title]
        try:
            self.save(target_page, orig_page)
        except requests.exceptions.HTTPError:
            time.sleep(60)
            self.save(target_page, orig_page)

        doc = self.loadout.client.pages[orig_page.name + '/doc']
        if doc.exists:
            self.copy_page(doc)

    def save(self, target_page: Page, orig_page: Page):
        text = orig_page.text()

        self.target.save(target_page, text, summary=self.summary)

    def append(self, target_page: Page, text: str):
        print(target_page.name)
        self.target.append(target_page, text, summary=self.summary)

    def move(self):

        # get the localized name for the template namespace
        old_template = self.target.client.namespaces[10] + ':Main page/'

        for orig_page in self.target.client.categories['Main page boxes']:
            if orig_page.name.startswith(old_template):

                # Replace "Template:Main page/" with "<main page name>/"
                new_title = orig_page.name.replace(old_template, self.target_main_page.name + '/')

                # I'm intentionally not suppressing a redirect in case of any unexpected links
                orig_page.move(new_title, reason = self.summary)
                print(f'Moved \"{orig_page.name}\" to \"{new_title}\"')

    def purge_main_page(self):
        self.target_main_page.purge()
        print(f"Purged {self.target_main_page.name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--update-only', action='store_true', default=UPDATE_ONLY)
    parser.add_argument('-i', '--is-import', action='store_true', default=IS_IMPORT)
    parser.add_argument('wikis', nargs='*', default=WIKIS)
    args = parser.parse_args()
    
    parsed_args = dict(
        update_only = args.update_only,
        is_import = args.is_import
    )

    if args.update_only and args.is_import:
        print('Arguments --update-only (-u) and --is-import (-i) are incompatible with each other.')
        return

    print(f"Running PIMP on the following wikis:\n{args.wikis}")
    if args.update_only:
        print("Running in update-only mode, mp boxes will not have their content changed.")
    if args.is_import:
        print("Running in import mode, Only content boxes will be added.")

    for wiki in args.wikis:
        name, lang = wiki, None
        if ':' in wiki:
            name, lang = wiki.split(':')
        Loadout(name, lang, **parsed_args).run()

if __name__ == '__main__':
    main()
