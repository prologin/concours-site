#!/bin/bash

BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOTDIR=$(dirname "$BASEDIR")
LIBDIR="$ROOTDIR/prologin/prologin/static/lib"
CACHEDIR="$BASEDIR/cache"

source "$BASEDIR/libs-tools.sh"
set -e

jquery() {
    with jquery 3.x.x https://github.com/jquery/jquery.git
    extract dist/jquery.min.js js
}

bootstrap() {
    with bootstrap v3.x.x https://github.com/twbs/bootstrap.git
    extract dist/css/bootstrap.min.css css
    extract dist/js/bootstrap.min.js js
}

fontawesome() {
    with fontawesome v4.x.x https://github.com/FortAwesome/Font-Awesome.git
    extract css/font-awesome.min.css css
    extract fonts .
}

select2() {
    with select2 4.x.x https://github.com/ivaynberg/select2.git
    extract dist/css/select2.min.css css
    extract dist/js/select2.min.js js
    extract dist/js/i18n/en.js js/i18n
    extract dist/js/i18n/fr.js js/i18n
}

typeahead() {
    with typeahead v1.x.x https://github.com/corejavascript/typeahead.js.git
    extract dist/typeahead.jquery.min.js js
}

datatables() {
    LIBS=(DataTables Responsive Select)
    ZIP="$CACHEDIR/datatables.zip"
    # -- parse versionsé
    data=$(curl -sL "https://datatables.net/download/index" | grep -F 'var _libraries' | cut -d= -f2 | sed 's|\\/|/|g')
    exts='bs'
    for lib in ${LIBS[@]}; do
        version=$(echo "$data" | jq -r 'to_entries[] | select(.value.name == "'$lib'") | .value."short-name" + "-" + .value.version' 2>/dev/null || true)
        echo "$lib: $version"
        exts="$exts/$version"
    done
    # -- download and extract relevant files from generated zip
    download "https://datatables.net/download/builder?$exts" "$ZIP"
    mkdir -p "$LIBDIR/js" "$LIBDIR/css"
    unzip -q -o -j -d "$LIBDIR/js" "$ZIP" datatables.min.js
    unzip -q -o -j -d "$LIBDIR/css" "$ZIP" datatables.min.css
}

mathjax() {
    ZIP="$CACHEDIR/mathjax.zip"
    TMPDIR="$CACHEDIR/MathJax-master"
    DIR="$LIBDIR/mathjax"
    download https://github.com/mathjax/MathJax/archive/master.zip "$ZIP"
    unzip -q -o "$ZIP" -d "$CACHEDIR"
    mkdir -p "$DIR"
    # MathJax interpretation of modularity: download 250MB of files in
    # a stupid folder hierarchy, then delete the files you don't need.
    # I am so done of this.
    # Inspired by https://github.com/mathjax/MathJax-grunt-cleaner/blob/master/Gruntfile.js
    keep () {
        copy "$TMPDIR" "$DIR" "$1"
    }
    # base files
    keep 'LICENSE'
    keep 'MathJax.js'
    keep 'jax/element/mml'
    # support TeX input only
    keep 'jax/input/TeX'
    # support HTML/CSS and TeX source output only
    keep 'jax/output/HTML-CSS'
    keep 'jax/output/PlainSource'
    # French i18n (English is already builtin)
    keep 'localization/fr'
    # keep the TeX font only, without the pngs & svgs
    keep 'fonts/HTML-CSS/TeX/eot'
    keep 'fonts/HTML-CSS/TeX/otf'
    keep 'fonts/HTML-CSS/TeX/woff'
    # some dependencies
    keep 'extensions/HTML-CSS'
    keep 'extensions/TeX'
    keep 'extensions/jsMath2jax.js'
    keep 'extensions/tex2jax.js'
    # misc extensions for UI & stuff
    keep 'extensions/FontWarnings.js'
    keep 'extensions/HelpDialog.js'
    keep 'extensions/MatchWebFonts.js'
    keep 'extensions/MathEvents.js'
    keep 'extensions/MathMenu.js'
    keep 'extensions/MathZoom.js'
    keep 'extensions/Safe.js'
    keep 'extensions/CHTML-preview.js'
}

mkdir -p "$CACHEDIR"

jquery
bootstrap
fontawesome
select2
typeahead
datatables
mathjax
