MANAGE = cd prologin && ./manage.py
TX = tx --debug

runserver:
	$(MANAGE) runserver

smtpserver:
	python -m smtpd -n -c DebuggingServer localhost:1025

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