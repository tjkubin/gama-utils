.PHONY: prep adj coord

all: prep ajd coord

prep:
	../mapa2gkf.awk -v dir=10 dist="1 1.5" meas.asc > meas.gkf
	../coord2gkf.py --xyz sour_xyz.txt < meas.gkf > meas.gkfc

adj:
	gama-local --svg adj.svg --algorithm envelope --xml adj.xml --text adj.txt meas.gkfc

coord:
	../gamaxml2txt.py --covmat cm.txt < adj.xml > coord.txt
	../coord_diff.m cm.txt 3 1 2 > diff.txt

clean:
	rm -f *.gkf *.gkfc *.xml *.txt *.svg
