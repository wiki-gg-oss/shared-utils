# Move old IMP box page names (Template:Main page/about) to new format (Default Loadout Wiki/about)
from mwcleric import AuthCredentials
from mwcleric import WikiggClient

WIKIS = ['gg:en']


class Loadout:
    summary = 'Bot: Updating name of IMP box pages'

    def __init__(self, target_name, target_lang):
        credentials = AuthCredentials(user_file="me")  # set to True iff the wiki is onboarding
        self.target_name = target_name
        self.target_lang = target_lang
        self.loadout = WikiggClient('defaultloadout')
        self.target = WikiggClient(target_name, credentials=credentials, lang=target_lang)  # edit the wiki here

        self.main_page = self.target.client.pages[self.target.client.site['mainpage']]

    def run(self):

        # move the pages
        self.move()

        # then purge the main page so the changes reflect
        self.purge_main_page()

        print("Done.")

    def move(self):

        old_template = 'Template:Main page/'

        for orig_page in self.target.client.categories['Main page boxes']:
            if orig_page.name.startswith(old_template):

                # Replace "Template:Main page/" with "<main page name>/"
                new_title = orig_page.name.replace(old_template, self.main_page.name + '/')

                # I'm intentionally not suppressing a redirect in case of any unexpected links
                orig_page.move(new_title, reason = self.summary)
                print(f'Moved \"{orig_page.name}\" to \"{new_title}\"')

    def purge_main_page(self):
        self.main_page.purge()
        print(f"Purged {self.main_page.name}")


if __name__ == '__main__':
    for wiki in WIKIS:
        if ':' in wiki:
            name, lang = wiki.split(':')
            Loadout(name, lang).run()
        else:
            Loadout(wiki, None).run()
