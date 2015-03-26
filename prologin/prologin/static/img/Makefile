SVGRASTERTRIM = inkscape --export-area-drawing
SVGRASTER = inkscape --export-area-page
CONVERT = convert
PNGOPTIMIZE = optipng -quiet -clobber -preserve

OBJS := logo_cube.png small_cube.png silhouette.png
AUXOBJS := small_cube.alone.png small_cube.alone.big.png

AUXOBJS := $(AUXOBJS) $(OBJS:.png=.big.png) $(OBJS:.png=.png.bak)

# Targets

silhouette.big.png: silhouette.svg
	$(SVGRASTER) -h 112 --export-png $@ $<

logo_cube.big.png: cube_perfect.svg
	$(SVGRASTERTRIM) -w 100 --export-png $@ $<

small_cube.alone.big.png: cube_perfect_smallonly.svg
	$(SVGRASTERTRIM) -h 80 --export-png $@ $<

small_cube.big.png: small_cube.alone.png
	$(CONVERT) $< -bordercolor '#35479a' -border 16x0 $@

# Generics

%.big.png: %.svg
	$(SVGRASTER) --export-png $@ $<

%.png: %.big.png
	$(PNGOPTIMIZE) -out $@ $<

# Main rules

all: $(OBJS)

clean-aux:
	$(RM) $(AUXOBJS)

clean: clean-aux
	$(RM) $(OBJS)

.PHONY: all clean clean-aux
