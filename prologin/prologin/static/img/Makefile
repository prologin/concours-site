logo_cube.png: cube_perfect.svg
	inkscape --export-area-drawing -w 100 --export-png $@ $<

small_cube.alone.png: cube_perfect_smallonly.svg
	inkscape --export-area-drawing -h 80 --export-png $@ $<

small_cube.png: small_cube.alone.png
	convert $< -bordercolor '#35479a' -border 16x0 $@

all: logo_cube.png small_cube.png

clean:
	rm logo_cube.png small_cube.alone.png small_cube.png

.PHONY: all clean
