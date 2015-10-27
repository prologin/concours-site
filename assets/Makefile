TOP := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
STATIC_DIR := $(dir $(TOP))prologin/prologin/static
IMG_DIR := $(STATIC_DIR)/img
LIB_DIR := $(STATIC_DIR)/lib

SVGRASTERTRIM := inkscape --export-area-drawing
SVGRASTER := inkscape --export-area-page
CONVERT := convert
PNGOPTIMIZE := optipng -quiet -clobber -preserve

JUMBOTRON_BG := "'#35479a'"
EMOJI_SIZE := 20
FAVICON_PNG_SIZES := 16 32 96 194
FAVICON_ICO_SIZES := 16 32 48
APPLE_TOUCH_SIZES := 57 60 72 76 114 120 144 152 180
MSTILE_SIZES := 144x144 150x150 310x150 310x310

OBJS := $(addprefix $(IMG_DIR)/,logo_cube.png small_cube.png silhouette.png prologin_emoji.png apple-touch-icon.png favicon.ico)
OBJS += $(patsubst %,$(IMG_DIR)/favicon-%.png,$(FAVICON_PNG_SIZES))
OBJS += $(patsubst %,$(IMG_DIR)/apple-touch-icon-%.png,$(APPLE_TOUCH_SIZES))
OBJS += $(patsubst %,$(IMG_DIR)/mstile-%.png,$(MSTILE_SIZES))

#AUXOBJS := $(addprefix $(IMG_DIR)/,small_cube.alone.png small_cube.alone.big.png)
#AUXOBJS := $(AUXOBJS) $(OBJS:.png=.big.png) $(OBJS:.png=.png.bak)

# Targets

$(IMG_DIR)/silhouette.big.png: silhouette.svg
	$(SVGRASTER) -h 112 --export-png $@ $<

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
	ln -s $< $@

# Generics

%.big.png: %.svg
	$(SVGRASTER) --export-png $@ $<

%.png: %.big.png
	$(PNGOPTIMIZE) -out $@ $<

$(IMG_DIR)/favicon-%.big.png: cube_perfect.svg
	$(SVGRASTERTRIM) -w $* --export-png $@ $<

$(IMG_DIR)/favicon-apple-%.png: cube_perfect.svg
	$(SVGRASTERTRIM) -w $(shell python -c 'print(int($* * 0.75))') --export-png $@ $<

$(IMG_DIR)/apple-touch-icon-%.big.png: $(IMG_DIR)/favicon-apple-%.png
	$(CONVERT) $< -gravity center -background white -extent $*x$* $@

$(IMG_DIR)/favicon-mstile-%.png: cube_perfect.svg
	$(SVGRASTERTRIM) -w $(shell python -c 'print(min(map(int, "$*".split("x"))) * 0.75)') --export-png $@ $<

$(IMG_DIR)/mstile-%.big.png: $(IMG_DIR)/favicon-mstile-%.png
	$(CONVERT) $< -gravity center -background transparent -extent $* $@

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

all: all-assets update-libs update-emojis

#clean-aux:
#	$(RM) $(AUXOBJS)

clean:
	$(RM) $(OBJS) $(LIB_DIR)/*

.PHONY: all update-libs update-emojis clean
