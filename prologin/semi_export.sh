#!/bin/sh
# Copyright (C) <2016> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

if [ $(id -u) -eq 0 ]; then
  if [ "$#" -ne 1 ]; then
    echo "please specify the file path to save the export to"
    exit 1
  fi
  echo -n "stopping website service..."
  systemctl stop website
  echo -e "\tDone !"
  cd `dirname $0`
  su prologin -c "pew in prologin-site sh `basename $0` `realpath $1`"
  systemctl start website
  exit 0
fi

export DJANGO_SETTINGS_MODULE=prologin.settings.semifinal
echo -n "Dumping database..."
cd `dirname $0`
./manage.py semifinal_export $1
