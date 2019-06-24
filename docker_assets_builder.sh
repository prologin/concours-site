#!/bin/sh
# Copyright (C) <2018> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

set -e

base="$(dirname "$0")"

docker build -t prologin-site "$base"

docker run --user "$UID" \
       --mount type=bind,source="$(realpath "$base")",destination=/var/prologin/site \
       -it prologin-site make assets
