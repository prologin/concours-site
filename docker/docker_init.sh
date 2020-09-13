#!/bin/sh

docker-compose build
docker-compose up -d
docker exec -it prologin_site sh -c '
cd prologin/assets
npm install
cd ..
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
python manage.py edition create
'
