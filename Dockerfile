FROM python:alpine

# requirements.txt
RUN apk add py3-pip git postgresql-dev curl-dev jpeg-dev gcc musl-dev libgcc curl libxslt-dev libxml2-dev libffi-dev

# various
RUN apk add bash

COPY requirements.txt requirements.txt
RUN mkdir -p /var/prologin/site && \
    pip3 install -r requirements.txt

# assets
RUN apk add inkscape optipng py-pygments imagemagick6 imagemagick6-dev make coreutils unzip jq

# help out python-wand
ENV MAGICK_HOME=/usr

WORKDIR /var/prologin/site
