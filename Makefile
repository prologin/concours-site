DIR = prologin
MANAGE = cd $(DIR) && ./manage.py
CELERY = cd $(DIR) && celery
TX = tx --debug

# Development servers and workers
# NOT SUITABLE FOR USE IN PRODUCTION.

runserver:
	$(MANAGE) runserver 0.0.0.0:8000

smtpserver:
	python -m smtpd -n -c DebuggingServer localhost:1025

celeryworker:
	$(CELERY) -l debug -A prologin worker

# Transifex

tx-push:
	$(MANAGE) makemessages -l en
	$(MANAGE) makemessages -a
	$(TX) push -s -t

tx-pull:
	mkdir -p "$(DIR)/locale"
	find "$(DIR)/locale" -mindepth 1 -maxdepth 1 -type d -exec rm -r "{}" \;
	$(TX) pull -l fr
	$(MANAGE) compilemessages

# Building/updating assets

assets:
	$(MAKE) all clean-aux -C assets

# Main rules

all: static-img

.PHONY: all runserver smtpserver celeryworker assets tx-push tx-pull
