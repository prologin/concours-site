TOP := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
STATIC_DIR := ../prologin/prologin/static
IMG_DIR := $(STATIC_DIR)/img
LIB_DIR := $(STATIC_DIR)/lib

SVGRASTERTRIM := inkscape --export-area-drawing
SVGRASTER := inkscape --export-area-page
CONVERT := convert
PNGOPTIMIZE := optipng -quiet -clobber -preserve

OBJS := $(addprefix $(IMG_DIR)/,logo_cube.png small_cube.png silhouette.png)
AUXOBJS := $(addprefix $(IMG_DIR)/,small_cube.alone.png small_cube.alone.big.png)

AUXOBJS := $(AUXOBJS) $(OBJS:.png=.big.png) $(OBJS:.png=.png.bak)

# Targets

$(IMG_DIR)/silhouette.big.png: silhouette.svg
	$(SVGRASTER) -h 112 --export-png $@ $<

$(IMG_DIR)/logo_cube.big.png: cube_perfect.svg
	$(SVGRASTERTRIM) -w 100 --export-png $@ $<

$(IMG_DIR)/small_cube.alone.big.png: cube_perfect_smallonly.svg
	$(SVGRASTERTRIM) -h 80 --export-png $@ $<

$(IMG_DIR)/small_cube.big.png: $(IMG_DIR)/small_cube.alone.png
	$(CONVERT) $< -bordercolor '#35479a' -border 16x0 $@

# Generics

%.big.png: %.svg
	$(SVGRASTER) --export-png $@ $<

%.png: %.big.png
	$(PNGOPTIMIZE) -out $@ $<

# Main rules
update-libs:
	cd $(LIB_DIR) && python $(TOP)/update-libs.py

all: $(OBJS) update-libs

clean-aux:
	$(RM) $(AUXOBJS)

clean: clean-aux
	$(RM) $(OBJS) $(LIB_DIR)/*

.PHONY: all update-libs clean clean-aux
