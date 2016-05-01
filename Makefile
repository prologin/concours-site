DIR = prologin
MANAGE = cd $(DIR) && ./manage.py
CELERY = cd $(DIR) && celery
TX = tx --debug

# Main rules

all: assets

# Development servers and workers
# NOT SUITABLE FOR USE IN PRODUCTION.

runserver:
	$(MANAGE) runserver localhost:8000

smtpserver:
	python -m smtpd -n -c DebuggingServer localhost:1025

celeryworker:
	$(CELERY) -l debug -A prologin worker

ifeq (manage,$(firstword $(MAKECMDGOALS)))
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(RUN_ARGS):;@:)
endif

manage:
	$(MANAGE) $(RUN_ARGS)

# Transifex

tx-push:
	$(MANAGE) makemessages -l en
	$(MANAGE) makemessages -a
	sed -i '/"Plural-Forms: nplurals=INTEGER; plural=EXPRESSION;\\n"/d' prologin/locale/en/LC_MESSAGES/django.po
	$(TX) push -s -t

tx-pull:
	mkdir -p "$(DIR)/locale"
	find "$(DIR)/locale" -mindepth 1 -maxdepth 1 -type d -exec rm -r "{}" \;
	$(TX) pull -l fr
	$(MANAGE) compilemessages

# Building/updating assets

assets:
	$(MAKE) all clean-aux -C assets

.PHONY: all runserver smtpserver celeryworker assets tx-push tx-pull
