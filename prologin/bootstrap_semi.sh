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

if [ -f "$1" ]; then
  export DJANGO_SETTINGS_MODULE=prologin.settings.semifinal
  echo -n "Dumping database..."
  pg_dump site > "dbdump_`date +"%m-%d-%y-%H-%M-%S"`.sql"
  echo -e "\t\tDone !"
  dropdb site
  createdb site
  ./manage.py migrate
  ./manage.py semifinal_bootstrap $1
else
  echo "no user data to import"
fi
