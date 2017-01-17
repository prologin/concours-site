TOP := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PROLOGIN_DIR := $(dir $(TOP))prologin
STATIC_DIR := $(PROLOGIN_DIR)/prologin/static
PUBLIC_DIR := $(dir $(TOP))public
IMG_DIR := $(STATIC_DIR)/img
LIB_DIR := $(STATIC_DIR)/lib

SVGRASTERTRIM := inkscape --export-area-drawing
SVGRASTER := inkscape --export-area-page
CONVERT := convert
PNGOPTIMIZE := optipng -quiet -clobber -preserve

JUMBOTRON_BG := '\#35479a'
EMOJI_SIZE := 20
FAVICON_PNG_SIZES := 16 32 36 48 72 96 144 192 194
FAVICON_ICO_SIZES := 16 32 48
APPLE_TOUCH_SIZES := 57 60 72 76 114 120 144 152 180
MSTILE_SIZES := 70x70 144x144 150x150 310x150 310x310
ARCHIVE_PLACEHOLDER_SIZE = 716
ERROR_503_LANGS := en fr

ARCHIVE_PLACEHOLDER := $(PROLOGIN_DIR)/archives/static/img/archive-placeholder.png

ERROR_503_TPLS := $(addsuffix .html,$(addprefix $(PUBLIC_DIR)/503.,$(ERROR_503_LANGS)))

OBJS := $(addprefix $(IMG_DIR)/,logo_cube.png small_cube.png silhouette.png prologin_emoji.png apple-touch-icon.png favicon.ico)
OBJS += $(patsubst %,$(IMG_DIR)/favicon-%.png,$(FAVICON_PNG_SIZES))
OBJS += $(patsubst %,$(IMG_DIR)/apple-touch-icon-%.png,$(APPLE_TOUCH_SIZES))
OBJS += $(patsubst %,$(IMG_DIR)/mstile-%.png,$(MSTILE_SIZES))
OBJS += $(ARCHIVE_PLACEHOLDER)
OBJS += $(ERROR_503_TPLS)

# Targets

all: all-assets update-libs update-emojis

$(IMG_DIR)/silhouette.big.png: silhouette.svg
	$(SVGRASTER) -h 220 --export-png $@ $<

$(IMG_DIR)/logo_cube.big.png: cube_perfect.svg
	$(SVGRASTERTRIM) -w 100 --export-png $@ $<

$(IMG_DIR)/small_cube.alone.big.png: cube_perfect_smallonly.svg
	$(SVGRASTERTRIM) -h 80 --export-png $@ $<

$(IMG_DIR)/prologin_emoji.big.png: cube_perfect_smallonly.svg
	$(SVGRASTERTRIM) -h $(EMOJI_SIZE) --export-png $@ $<

$(IMG_DIR)/small_cube.big.png: $(IMG_DIR)/small_cube.alone.png
	$(CONVERT) $< -bordercolor $(JUMBOTRON_BG) -border 16x0 $@

$(IMG_DIR)/favicon.ico: $(patsubst %,$(IMG_DIR)/favicon-%.big.png,$(FAVICON_ICO_SIZES))
	$(CONVERT) $^ $@

$(IMG_DIR)/apple-touch-icon.png: $(IMG_DIR)/apple-touch-icon-180.png
	cp $< $@

$(ARCHIVE_PLACEHOLDER): $(IMG_DIR)/favicon-apple-500.png
	$(CONVERT) $< -gravity center -background $(JUMBOTRON_BG) -extent $(ARCHIVE_PLACEHOLDER_SIZE)x$(ARCHIVE_PLACEHOLDER_SIZE) $@

# Generics

%.big.png: %.svg
	$(SVGRASTER) --export-png $@ $<

%.png: %.big.png
	$(PNGOPTIMIZE) -out $@ $<

$(IMG_DIR)/favicon-%.big.png: cube_perfect_smallonly.svg
	$(SVGRASTERTRIM) -w $* --export-png $@ $<

$(IMG_DIR)/favicon-apple-%.png: cube_perfect.svg
	$(SVGRASTERTRIM) -w $(shell python -c 'print(int($* * 0.7))') --export-png $@ $<

$(IMG_DIR)/apple-touch-icon-%.big.png: $(IMG_DIR)/favicon-apple-%.png
	$(CONVERT) $< -gravity center -background white -extent $*x$* $@

$(IMG_DIR)/favicon-mstile-%.png: cube_perfect.svg
	$(SVGRASTERTRIM) -w $(shell python -c 'print(min(map(int, "$*".split("x"))) * 0.55)') --export-png $@ $<

$(IMG_DIR)/mstile-%.big.png: $(IMG_DIR)/favicon-mstile-%.png
	$(CONVERT) $< -gravity center -background transparent -extent $* $@

$(PUBLIC_DIR)/503.%.html:
	cd $(PROLOGIN_DIR) && python manage.py statictemplate 503.html $* -f $@

print-%:
	@echo '$*=$($*)'

# Main rules

update-libs:
	mkdir -p $(LIB_DIR)
	cd $(LIB_DIR) && python $(TOP)/update-libs.py

update-emojis:
	cd $(STATIC_DIR) && python $(TOP)/update-emojis.py
	mogrify -resize $(EMOJI_SIZE)x $(IMG_DIR)/emojis/*.png

all-assets: $(OBJS)

clean-assets:
	$(RM) $(OBJS)

clean:
	$(RM) $(OBJS) $(LIB_DIR)/*

.PHONY: all update-libs update-emojis clean
