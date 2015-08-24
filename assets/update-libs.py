#!/usr/bin/env python

import io
import os
import requests
import shutil
import subprocess
import zipfile

DEV_SUFFIXES = {'dev', 'alpha', 'beta'}


def strip_components(path, n):
    path = os.path.normpath(path)
    return os.sep.join(path.split(os.sep)[n:])


def extract_from_zip(zipball, member, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipball.open(member) as source, open(path, 'wb') as target:
        shutil.copyfileobj(source, target)


def pygments(path='css/pygments-{theme}.css', theme='monokai', prefix='.pyg-hl'):
    path = path.format(theme=theme)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as stdout:
        subprocess.check_call(['pygmentize', '-S', theme, '-f', 'html', '-a', prefix], stdout=stdout)
    print("Wrote", path)


def jquery(path='js/jquery.min.js'):
    print("Updating jQuery JS")
    tags = requests.get('https://api.github.com/repos/jquery/jquery/tags').json()
    # most recent production 2.* release
    tag = [tag for tag in tags if all(p not in tag['name'] for p in DEV_SUFFIXES) and tag['name'].startswith("2")][0]
    print("Tag is", tag['name'])
    url = 'https://code.jquery.com/jquery-{}.min.js'.format(tag['name'])
    print("Downloading", url)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with requests.get(url, stream=True).raw as source, open(path, 'wb') as target:
        source.decode_content = True
        shutil.copyfileobj(source, target)


def bootstrap():
    print("Updating Bootstrap CSS/JS")
    releases = requests.get('https://api.github.com/repos/twbs/bootstrap/releases').json()
    # most recent production release
    release = [rel for rel in releases if all(p not in rel['tag_name'] for p in DEV_SUFFIXES)][0]
    print("Release is", release['tag_name'])
    zipball_url = release['zipball_url']
    print("Downlading", zipball_url)
    zipball = io.BytesIO(requests.get(zipball_url).content)
    with zipfile.ZipFile(zipball) as zipball:
        for member in zipball.namelist():
            path = strip_components(member, 1)  # strip root dir
            if path in ('dist/css/bootstrap.min.css', 'dist/js/bootstrap.min.js') or path.startswith('dist/fonts/'):
                path = strip_components(path, 1)  # strip dist/
                extract_from_zip(zipball, member, path)
                print("Extracted", path)


def font_awesome():
    print("Updating Fontawesome CSS")
    tags = requests.get('https://api.github.com/repos/FortAwesome/Font-Awesome/tags').json()
    # most recent production release
    tag = [tag for tag in tags if all(p not in tag['name'] for p in DEV_SUFFIXES)][0]
    print("Tag is", tag['name'])
    zipball_url = tag['zipball_url']
    print("Downloading", zipball_url)
    zipball = io.BytesIO(requests.get(zipball_url).content)
    with zipfile.ZipFile(zipball) as zipball:
        for member in zipball.namelist():
            path = strip_components(member, 1)  # strip root dir
            if path == 'css/font-awesome.min.css' or path.startswith('fonts/'):
                extract_from_zip(zipball, member, path)
                print("Extracted", path)


def google_font(font_name, font_variants={'regular'}, font_formats={'woff', 'woff2'},
                url_prefix='', css_name='gfont-{font}.css', font_dir='fonts'):
    font_face = (
        "/* {fid}-{vid} - {subset} */ @font-face {{ "
        "font-family: {family}; font-style: {style}; font-weight: {weight}; src: {sources}; "
        "}}")
    font_face_source = "url('{pref}{fid}-{ver}-{subset}-{vid}.{fmt}') format('{fmt}')"
    font_url = 'https://google-webfonts-helper.herokuapp.com/api/fonts/{}'.format(font_name)

    print("Updating {} Google font with {} variants".format(font_name, len(font_variants)))
    font = requests.get(font_url).json()
    font_id = font['id']
    variants_map = {v['id']: v for v in font['variants']}
    css_data = []
    for variant_id in font_variants:
        try:
            variant = variants_map[variant_id]
        except KeyError:
            raise KeyError("Variant does not exist: {}".format(variant_id))

        sources = ["local('{}')".format(local) for local in variant['local']]
        sources.extend([
            font_face_source.format(
                fmt=fmt,
                pref=url_prefix,
                fid=font_id,
                ver=font['version'],
                subset=font['defSubset'],
                vid=variant_id)
            for fmt, url in variant.items()
            if fmt in font_formats])
        sources = ', '.join(sources)

        css_data.append(font_face.format(
            fid=font_id,
            vid=variant_id,
            subset=font['defSubset'],
            family=variant['fontFamily'],
            style=variant['fontStyle'],
            weight=variant['fontWeight'],
            sources=sources,
        ))

    css_path = css_name.format(font=font_id)
    os.makedirs(os.path.dirname(css_path), exist_ok=True)
    with open(css_path, 'w') as css_file:
        css_file.write('\n'.join(css_data))
    print("Wrote CSS file", css_path)

    font = requests.get(font_url, params={'download': 'zip',
                                          'subsets': font['defSubset'],
                                          'formats': ','.join(font_formats),
                                          'variants': ','.join(font_variants)})
    os.makedirs(font_dir, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(font.content)) as zipball:
        zipball.extractall(path=font_dir)
        print("\n".join("Extracted {}".format(os.path.join(font_dir, name)) for name in zipball.namelist()))


def main():
    pygments()
    jquery()
    bootstrap()
    font_awesome()
    google_font('roboto',
                font_variants={'regular', '300', '300italic'},
                url_prefix='../fonts/',
                css_name='css/gfont-{font}.css')

if __name__ == '__main__':
    main()
