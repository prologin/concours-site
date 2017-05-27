TOP = $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
DIR = $(TOP)/prologin
LOCALE_DIR = $(DIR)/locale
MANAGE = cd $(DIR) && ./manage.py
CELERY = cd $(DIR) && celery
TX = tx --debug
PORT = 8000
SMTP_PORT = 1025

# Main rules

all: assets

# Development servers and workers
# NOT SUITABLE FOR USE IN PRODUCTION.

runserver:
	$(MANAGE) runserver localhost:$(PORT)

smtpserver:
	python -c 'import smtpd, asyncore; smtpd.DebuggingServer(("0.0.0.0", $(SMTP_PORT)), None); asyncore.loop()'

celeryworker:
	$(CELERY) -l debug -A prologin worker

# Transifex

tx-push:
	$(MANAGE) makemessages -l en
	$(MANAGE) makemessages -a
	sed -i '/"Plural-Forms: nplurals=INTEGER; plural=EXPRESSION;\\n"/d' $(LOCALE_DIR)/en/LC_MESSAGES/django.po
	$(TX) push -s -t

tx-pull:
	mkdir -p '$(LOCALE_DIR)'
	find '$(LOCALE_DIR)' -mindepth 1 -maxdepth 1 -type d -exec rm -r "{}" \;
	$(TX) pull -l fr
	$(MANAGE) compilemessages

# Building/updating assets

assets:
	$(MAKE) -C assets all

.PHONY: all runserver smtpserver celeryworker assets tx-push tx-pull
