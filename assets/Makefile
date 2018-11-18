# Main directories
TOP := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PROLOGIN_DIR := $(dir $(TOP))prologin
STATIC_DIR := $(PROLOGIN_DIR)/prologin/static
PUBLIC_DIR := $(dir $(TOP))public
IMG_DIR := $(STATIC_DIR)/img
CSS_DIR := $(STATIC_DIR)/css

# First target must be 'all'
all: assets

include config.mk

# All objects
OBJS :=
# -- images
include images.mk
# -- error templates
ERRORTEMPLATES := $(addprefix $(PUBLIC_DIR)/503.,$(ERROR_503_LANGS))
ERRORTEMPLATES := $(addsuffix .html,$(ERRORTEMPLATES))
OBJS += $(ERRORTEMPLATES)

# Error templates
$(PUBLIC_DIR)/503.%.html:
	cd $(PROLOGIN_DIR) && python manage.py statictemplate 503.html \
		--language-code $* -f $@

errortemplates: $(ERRORTEMPLATES)

# Pygments CSS theme
$(PYGMENTS_CSS):
	mkdir -p $(dir $(@))
	pygmentize -S $(PYGMENTS_THEME) -a $(PYGMENTS_PREFIX) -f html >$@

# Debug rule
print-%:
	@echo '$*=$($*)'

# Main rules

assets: $(OBJS)

clean:
	$(RM) -r $(OBJS)

.PHONY: all errortemplates assets clean
