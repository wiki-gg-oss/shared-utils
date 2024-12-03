import argparse
import time

import requests
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from requests.exceptions import HTTPError
from mwcleric import AuthCredentials, WikiggClient
from mwcleric.errors import RetriedLoginAndStillFailed


WIKIS = ['gg:en']
NAMESPACES = []
EXCLUDE_NAMESPACES = False
DO_NULL_EDITS = False
FROM_PAGE = ''
THREAD_COUNT = 1
DO_WARMUP_CACHE_MAYBE = False


class PurgeBot:
    namespaces: list[int]
    do_null: bool
    start_at: str
    thread_count: int = 1
    warmup: bool

    def __init__(self,
                 target_name,
                 target_lang,
                 namespaces,
                 exclude_namespaces,
                 do_null,
                 thread_count,
                 start_at,
                 warmup):
        self.passed_startat = False
        credentials = AuthCredentials(user_file="me")
        self.target_name = target_name
        self.target_lang = target_lang
        self.namespaces = namespaces
        self.do_null = do_null
        self.start_at = start_at
        self.warmup = warmup

        self.target = WikiggClient(target_name, credentials=credentials, lang=target_lang)

        if not namespaces:
            self.namespaces = self.target.client.namespaces

        if namespaces and exclude_namespaces:
            self.namespaces = [item for item in self.target.client.namespaces if item not in namespaces]

        if thread_count > 1:
            self.thread_count = thread_count

    def run(self):
        for ns in self.namespaces:
            self.process_namespace(ns)

    def process_namespace(self, ns, pool: ThreadPoolExecutor|None=None):
        if ns < 0:
            print(f'Namespace cannot be edited: {ns}')
            return

        if ns not in self.target.client.namespaces:
            print(f'Remote wiki does not have namespace #{ns}')
            return

        if self.thread_count > 1 and not pool:
            with ThreadPoolExecutor(max_workers=self.thread_count) as pool:
                return self.process_namespace(ns, pool)

        print(f'Purging namespace #{ns}')
        for page in self.target.client.allpages(namespace=ns):
            if self.start_at:
                if page.name.startswith(self.start_at):
                    self.start_at = None
                else:
                    continue

            if pool:
                pool.submit(self.process_page, page)
            else:
                self.process_page(page)

    def process_page(self, page):
        while True:
            try:
                print(page.name)
                if self.do_null:
                    self.target.touch(page)
                self.target.purge(page)

                if self.warmup:
                    encoded_name = urllib.parse.quote(page.name)
                    article_url = f'https://{self.target.url}{self.target.path}wiki/{encoded_name}'
                    response = requests.get(article_url)
                    if response.status_code >= 400:
                        print('HTML cache warm-up failed:', article_url)

                break
            except (HTTPError, RetriedLoginAndStillFailed) as e:
                print(e)
                time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--namespaces', type=int, nargs='*', default=NAMESPACES)
    parser.add_argument('-x', '--exclude-namespaces', action='store_true', default=EXCLUDE_NAMESPACES)
    parser.add_argument('-e', '--nulledit', action='store_true', default=DO_NULL_EDITS)
    parser.add_argument('-t', '--threads', type=int, default=THREAD_COUNT)
    parser.add_argument('-f', '--start-at', type=str, default=FROM_PAGE)
    parser.add_argument('-w', '--warmup', action='store_true', default=DO_WARMUP_CACHE_MAYBE)
    parser.add_argument('wikis', nargs='*', default=WIKIS)
    args = parser.parse_args()

    common_bot_args = dict(
        do_null=args.nulledit,
        namespaces=args.namespaces,
        exclude_namespaces=args.exclude_namespaces,
        thread_count=args.threads,
        start_at=args.start_at,
        warmup=args.warmup,
    )

    for wiki in args.wikis:
        name, lang = wiki, None
        if ':' in wiki:
            name, lang = wiki.split(':')
        PurgeBot(name, lang, **common_bot_args).run()

