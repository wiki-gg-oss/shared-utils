from mwcleric.wikigg_client import WikiggClient
from mwcleric.auth_credentials import AuthCredentials

WIKIS = ['test:en']

class fixDoubleRedirects:
    def __init__(self, wiki, lang):
        self.credentials = AuthCredentials(user_file="me")
        self.wiki = WikiggClient(wiki, credentials=self.credentials, lang=lang)
        self.lang = lang
        self.pairs = {}
        self.targets = []

    def run(self):
        self.build_pairs()

        for name in self.targets:
            self.save(name, self.get_final(name))

    def build_pairs(self) -> None:
        args = {
            "format": "json",
            "list": "querypage",
            "formatversion": "2",
            "qppage": "DoubleRedirects"
        }

        response = self.wiki.client.get('query', **args)

        data = response['query']['querypage']['results']
        for page in data:
            self.targets.append(page['title'])

            # we're doing this twice to create a list of redirect targets for the chain, instead of just the end result
            # this will let us process triple, quadruple, etc. redirects in one pass
            self.pairs[page['title']] = page['databaseResult']['b_title']
            self.pairs[page['databaseResult']['b_title']] = page['databaseResult']['c_title']

    def get_final(self, name:str) -> str:
        if name in self.pairs:
            return self.get_final(self.pairs[name])
        else:
            return name

    def save(self, name: str, target:str) -> None:
        text = f"#REDIRECT [[{target}]]"
        summary = f"Fixed double redirect. New target: [[{target}]]"

        try:
            self.wiki.save_title(name, text, summary=summary)
            print(f"[[{name}]] target changed to [[{target}]]")
        except:
            print(f"ERROR, could not save [[{name}]]")


def main():
    for wiki in WIKIS:
        name, lang = wiki.split(':')
        fixDoubleRedirects(name, lang).run()

if __name__ == '__main__':
    main()