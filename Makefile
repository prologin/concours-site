TOP = $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
DIR = $(TOP)/prologin
LOCALE_DIR = $(DIR)/locale
MANAGE = cd $(DIR) && PYTHONWARNINGS=once ./manage.py
REGIONAL_MANAGE = cd $(DIR) && DJANGO_SETTINGS_MODULE=prologin.settings.semifinal_dev ./manage.py
CELERY = cd $(DIR) && celery
TX = tx --debug
PORT = 8000
SMTP_HOST = 127.0.0.1
SMTP_PORT = 1025
SMTP_LAG = 0

# Main rules

all: assets

# Development servers and workers
# NOT SUITABLE FOR USE IN PRODUCTION.

runserver:
	$(MANAGE) runserver localhost:$(PORT)

regional-runserver:
	$(REGIONAL_MANAGE) runserver localhost:$(PORT)

smtpserver:
	python $(TOP)/smtp_debug.py --host $(SMTP_HOST) --port $(SMTP_PORT) --lag $(SMTP_LAG)

celeryworker:
	$(CELERY) -l debug -A prologin worker

# Test

test:
	$(MANAGE) test --settings=prologin.settings.test

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

.PHONY: all test runserver smtpserver celeryworker assets tx-push tx-pull
