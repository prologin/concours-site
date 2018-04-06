# Tools
SVGRASTERTRIM := inkscape --export-area-drawing
SVGRASTER := inkscape --export-area-page
CONVERT := convert
PNGOPTIMIZE := optipng -quiet -clobber -preserve

# Archive
ARCHIVE_PLACEHOLDER := $(PROLOGIN_DIR)/archives/static/img/archive-placeholder.png
OBJS += $(ARCHIVE_PLACEHOLDER)

# Favicons
# -- basic
OBJS += $(patsubst %,$(IMG_DIR)/favicon-%.png,$(FAVICON_PNG_SIZES))
# -- icons for apple devices/software
OBJS += $(patsubst %,$(IMG_DIR)/apple-touch-icon-%.png,$(APPLE_TOUCH_SIZES))
# -- icons for microsoft devices/software
OBJS += $(patsubst %,$(IMG_DIR)/mstile-%.png,$(MSTILE_SIZES))

# Other images
IMGS := favicon.ico \
# Used in main navbar \
    logo_cube.png \
# Used in homepage CSS \
    small_cube.png \
# default profile picture \
    silhouette.png
OBJS += $(addprefix $(IMG_DIR)/,$(IMGS))

# Targets

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
	$(CONVERT) $< \
	    -gravity center \
	    -background $(JUMBOTRON_BG) \
	    -extent $(ARCHIVE_PLACEHOLDER_SIZE)x$(ARCHIVE_PLACEHOLDER_SIZE) \
	    $@

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
	$(SVGRASTERTRIM) -w $(shell python -c 'print(min(map(int, "$*".split("x"))) * 0.55)') \
	    --export-png $@ \
	    $<

$(IMG_DIR)/mstile-%.big.png: $(IMG_DIR)/favicon-mstile-%.png
	$(CONVERT) $< \
	    -gravity center -background transparent \
	    -extent $* \
	    $@
