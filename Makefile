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
	$(MANAGE) makemessages -a
	$(TX) push -s -t

tx-pull:
	$(TX) pull -l fr
	$(MANAGE) compilemessages

# Subsystems

static-img:
	$(MAKE) all clean-aux -C prologin/prologin/static/img

# Main rules

all: static-img

.PHONY: all runserver static-img tx-push tx-pull
