#!/bin/sh

if [ $(id -u) -eq 0 ]; then
  echo -n "stopping website service..."
  systemctl stop website
  echo -e "\tDone !"
  cd /home/prologin/
  su prologin -c "pew in prologin-site sh $0 $1"
  systemctl start website
  exit 0
fi

export DJANGO_SETTINGS_MODULE=prologin.settings.semifinal
echo -n "Dumping database..."
cd `dirname $0`
./manage.py semifinal_export $1
