#!/bin/sh

docker exec -it prologin_site sh -c '
cd prologin
python manage.py migrate
python manage.py createsuperuser
python manage.py edition create
'
