import json
import os
import shutil
import subprocess
import tempfile


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='gemoji-') as dest_dir:
        subprocess.check_call(['git', 'clone', '--depth=1', 'git@github.com:github/gemoji.git', dest_dir])
        with open(os.path.join(dest_dir, 'db/emoji.json')) as f:
            emoji_db = json.load(f)
        emoji_db = (emoji for emoji in emoji_db if emoji.get('emoji'))
        name_to_char = {}
        for emoji in emoji_db:
            char = emoji['emoji']
            if len(char) > 1:
                if char[1] == '\ufe0f':
                    char = char[0]
            char = '-'.join('%x' % ord(c) for c in char)
            for alias in emoji['aliases']:
                name_to_char[alias] = char
        shutil.copytree(os.path.join(dest_dir, 'images/emoji/unicode'), 'img/emojis')

    with open('../utils/markdown/emoji_list.py', 'w') as f:
        f.write("EMOJIS = ")
        f.write(repr(name_to_char))
        f.write("\n")

    print("Imported {} emojis".format(len(name_to_char)))
