# Main directories
TOP := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PROLOGIN_DIR := $(dir $(TOP))prologin
STATIC_DIR := $(PROLOGIN_DIR)/prologin/static
PUBLIC_DIR := $(dir $(TOP))public
IMG_DIR := $(STATIC_DIR)/img
LIB_DIR := $(STATIC_DIR)/lib
CSS_DIR := $(STATIC_DIR)/css

# First target must be 'all'
all: assets libs

include config.mk

# All objects
OBJS :=
# -- images
include images.mk
# -- pygments
PYGMENTS_CSS := $(LIB_DIR)/css/pygments-$(PYGMENTS_THEME).css
OBJS += $(PYGMENTS_CSS)

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

libs: $(TOP)/libs.sh
	$<

clean-assets:
	$(RM) -r $(OBJS)

clean-libs:
	$(RM) -r $(LIB_DIR)/*

clean: clean-assets clean-libs

.PHONY: all errortemplates assets libs clean-assets clean-libs clean
