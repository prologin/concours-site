# These few lines of bash do more or less what bower does, without all the
# nodejs crap: find the right git tag and clone it.
# I don't want to rely on yet another package repository, be it npm or bower,
# so raw git URLs are used instead of some random package name from bower.

copy() {
    # copy /foo/bar /baz a/b/c
    # will recursively copy /foo/bar/a/b/c to /baz/a/b/c
    sourcedir="$1"
    targetdir="$2"
    source="$sourcedir/$3"
    dir=$(dirname "$3")
    target="$targetdir/$dir"
    mkdir -p "$target"
    cp -r -v "$source" "$target"
}

download() {
    curl -sL "$1" >"$2"
}

set _name _ver _url

_git_get() {
    # find the most recent version matching _ver pattern
    ver=${_ver//./'\.'}
    ver=${ver//x/[0-9]+}
    ref=$(git ls-remote --tags "$_url" | egrep "/tags/$ver\$" | sort --version-sort -r --key 2 | head -1 | cut -d/ -f3)
    [[ -z "$ref" ]] && exit 1
    dir="$CACHEDIR/$_name"
    rm -rf "$dir"
    git clone -c advice.detachedHead=false --depth 1 --branch "$ref" "$_url" "$dir"
}

with() {
    _name=$1
    _ver=$2
    _url=$3
    _git_get
}

extract() {
    target="$LIBDIR/$2"
    mkdir -p "$target"
    cp -v -r "$CACHEDIR/$_name/$1" "$target"
}
