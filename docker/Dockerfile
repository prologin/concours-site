FROM python:3.8-slim-buster

# requirements.txt
RUN apt update
RUN apt install -y python3 python3-venv python3-pip npm imagemagick \
    redis-server texlive git

RUN mkdir -p /var/prologin/site

COPY ../requirements.txt requirements.txt
RUN pip3 install -r requirements.txt


WORKDIR /var/prologin/site
