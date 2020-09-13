#!/bin/sh

docker-compose build && \
docker-compose up -d && \
docker exec -it prologin_site sh -c '
cd assets
npm install
' && \
docker exec -it prologin_site python prologin/manage.py migrate && \
docker exec -it prologin_site python prologin/manage.py collectstatic && \
docker exec -it prologin_site python prologin/manage.py createsuperuser && \
docker exec -it prologin_site python prologin/manage.py edition create