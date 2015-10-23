#!/usr/bin/env python

from update_utils import *
import json
import io
import os
import requests
import shutil
import tempfile
import zipfile

GEMOJI_ZIP_URL = 'https://github.com/github/gemoji/archive/master.zip'


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='gemoji-') as dest_dir:
        # Get github "gemoji" project, where emoji PNGs are stored
        zipball = io.BytesIO(requests.get(GEMOJI_ZIP_URL).content)
        with zipfile.ZipFile(zipball) as zipball:
            zipball.extractall(dest_dir, get_members_strip_prefix(zipball))

        with open(os.path.join(dest_dir, 'db/emoji.json')) as f:
            emoji_db = json.load(f)

        emoji_db = (emoji for emoji in emoji_db if emoji.get('emoji'))
        # Map emoji human name to PNG file name
        name_to_char = {}
        for emoji in emoji_db:
            char = emoji['emoji']
            if len(char) > 1:
                if char[1] == '\ufe0f':
                    char = char[0]
            char = '-'.join('%x' % ord(c) for c in char)
            for alias in emoji['aliases']:
                name_to_char[alias] = char
        # Copy the PNGs to static
        shutil.rmtree('img/emojis', ignore_errors=True)
        shutil.copytree(os.path.join(dest_dir, 'images/emoji/unicode'), 'img/emojis')

    # Little easter-egg
    shutil.copy2('img/prologin_emoji.png', 'img/emojis/prologin.png')
    name_to_char['prologin'] = 'prologin'

    # Emoji list for Markdown parsing
    with open('../utils/markdown/emoji_list.py', 'w') as f:
        f.write("EMOJIS = ")
        f.write(repr(name_to_char))
        f.write("\n")

    print("Imported {} emojis".format(len(name_to_char)))
