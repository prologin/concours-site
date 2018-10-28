#!/bin/sh

set -e

base="$(dirname "$0")"

docker build -t prologin-site "$base"

docker run --user "$UID" \
       --mount type=bind,source="$(realpath "$base")",destination=/var/prologin/site \
       -it prologin-site make assets
