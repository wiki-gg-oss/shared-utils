## How to use this script

1. Either use git to clone this repo or copy-paste the contents of `main.py` to a local directory.
2. Install the latest version of [mwcleric](https://github.com/RheingoldRiver/mwcleric) using `pip install -U mwcleric`
3. Set up a bot password for wiki.gg. Give it basic rights, editing pages, editing protected pages, changing protection levels of pages, moving pages, and editing system messages.
    * Note, usually you don't want to give passwords both edit system messages & high-volume editing, so try and use a unique password for just this one script.
4. Set the target to the wiki you want (by default, `gg.wiki.gg`, the testing wiki)
5. Run the script.
7. The first time you run the script, you'll be prompted by `AuthCredentials` to enter your username, bot name, and bot password. If you're using `use_site_pw=True` you'll also be asked for the user-pass combination to view the wiki.
    * If you don't set `use_site_pw=True` the first time you run the script, you can either make a new set of credentials and add the dev user/pass that time or add the fields `site_user` and `site_pw` to the json located at `~/.config/mwcleric/wiki_account_me.json` (e.g. for me on Windows this is `C:/Users/River/.config/mwcleric/wiki_account_me.json`)
