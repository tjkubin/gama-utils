#!/usr/bin/python 

# program pro import souradnic x, y, z do davky GKF (gama-local) 
# ze seznamu souradnic v textovem formatu
#
# pouziti:
#
# coord2gkf.py --yx=souradnice_xy.txt < sit.gkf > sit.s_body.gkf
#	seznam souradnic ma tvar id_bodu souradnice_y souradnice_x 
#	vlozene souradnice budou nastaveny jako fixni fix="xy"
#	ostatni jako urcovane adj="xy"
#
# coord2gkf.py --con --xyz=souradnice_xy.txt < sit.gkf > sit.s_body.gkf
#	vlozene souradnice budou nastaveny jako operne adj="XYZ"
#	ostatni jako urcovane adj="xyz"
#
# coord2gkf.py --con --force --xyz=souradnice_xy.txt < sit.gkf > sit.s_body.gkf
#	souradnice bodu, ktere se uz nachazeji v souboru sit.gkf
#	a take v seznamu souradnic budou prepsany podle souradnic v seznamu


# Autor: Tomas Kubin (2009)
# Instituce: SFv, CVUT v Praze, Katedra geodezie a pozemkovych uprav
# Licence: GPL

import sys
import re

# typy nacitanych seznamu souradnic
XY = 1
YX = 2
XYZ = 3
YXZ = 4
souradnice={XY:"xy", YX:"xy", XYZ:"xyz", YXZ:"xyz"}

# typy bodu
FIX = 0
CON = 1
ADJ = 2

# nacteni vstupnich parametru
from optparse import OptionParser
parser = OptionParser()
parser.add_option("", "--xy", dest="soubor_xy",
		help="seznam souradnic xy", metavar="FILE")
parser.add_option("", "--yx", dest="soubor_yx",
		help="seznam souradnic yx", metavar="FILE")
parser.add_option("", "--xyz", dest="soubor_xyz",
		help="seznam souradnic xyz", metavar="FILE")
parser.add_option("", "--yxz", dest="soubor_yxz",
		help="seznam souradnic yxz", metavar="FILE")
parser.add_option("", "--fix", action="store_true", dest="fix", default=False,
		help="typ vlozenych bodu se nastavi na \"fixed\"")
parser.add_option("", "--con", action="store_true", dest="con", default=False,
		help="typ vlozenych bodu se nastavi na \"constrained\"")
parser.add_option("", "--adj", action="store_true", dest="adj", default=False,
		help="typ vlozenych bodu se nastavi na \"adjusted\"")
parser.add_option("", "--force", action="store_true", dest="force", default=False,
		help="souradnice a typy v souboru budou prepsany hodnotami ze seznamu souradnic a podle typu --fix --adj a --con")
(options, args) = parser.parse_args();

# otevreni souboru se souradnicemi
try:
	if options.soubor_xy != None:
		filetype = XY;
		fname = options.soubor_xy
	if options.soubor_yx != None:
		filetype = YX;
		fname = options.soubor_yx
	if options.soubor_xyz != None:
		filetype = XYZ;
		fname = options.soubor_xyz
	if options.soubor_yxz != None:
		filetype = YXZ;
		fname = options.soubor_yxz
	file = open(fname);
except IOError:
	sys.stderr.write("Chyba pri otevirani souboru souradnic \"%s\"" % fname)
	sys.exit(1)

# nacteni typu bodu --adj --con --fix
if options.adj:
	typBodu = ADJ
elif options.con:
	typBodu = CON
else:
	typBodu = FIX

# prepsani souradnic --force
force = False
if options.force != None:
	force = True

# nacteni souboru
patt_xy = """
	^
	\s*
	([\S]+)		# cislo bodu
	\s+
	([\S]+)		# souradnice x
	\s+
	([\S]+)		# souradnice y
"""
patt_xyz = """
	^
	\s*
	([\S]+)		# cislo bodu
	\s+
	([\S]+)		# souradnice x
	\s+
	([\S]+)		# souradnice y
	\s+
	([\S]+)		# souradnice z
"""

line = file.readline()
sour = {}
line_num = 1
while line:
	#print line
	if filetype == XY or filetype == YX:
		search = re.search(patt_xy, line, re.VERBOSE)
	else:
		search = re.search(patt_xyz, line, re.VERBOSE)

	if search == None:
		sys.stderr.write("Chyba v souboru souradnic \"%s\" na radku %i\n" 
				% (fname, line_num))
		line = file.readline()
		line_num+=1
		continue
	group = search.groups()
	#print "Match: ", group[0]

	if filetype == XY:
		sour.update({group[0]:(group[1],group[2])})
	elif filetype == YX:
		sour.update({group[0]:(group[2],group[1])})
	elif filetype == XYZ:
		sour.update({group[0]:(group[1],group[2],group[3])})
	elif filetype == YXZ:
		sour.update({group[0]:(group[2],group[1],group[3])})
	else:
		sys.stderr.write("Chybny typ seznamu souradnic (filetype): %i" % filetype)

	line = file.readline()
	line_num+=1
file.close()
sys.stderr.write("Pocet nactenych bodu: %i\n" % len(sour.keys()))

# nacteni DOM
from xml.dom import minidom
dom = minidom.parse(sys.stdin);

def zapisAtribut(element, jmeno, hodnota, prepsat=False):
	if prepsat:
		element.setAttribute(jmeno, hodnota)
	elif not element.attributes.getNamedItem(jmeno):
		element.setAttribute(jmeno, hodnota)

def zapisTypBodu(element, typBodu, typSouradnic, prepsat):
	atts = element.attributes
	adj = atts.getNamedItem("adj")
	fix = atts.getNamedItem("fix")
	if prepsat:
		if adj: element.removeAttribute("adj")
		if fix: element.removeAttribute("fix")
	adj = atts.getNamedItem("adj")
	fix = atts.getNamedItem("fix")
	if not adj and not fix:
		if typBodu == FIX:
			zapisAtribut(element, "fix", souradnice[typSouradnic])
		if typBodu == ADJ:
			zapisAtribut(element, "adj", souradnice[typSouradnic])
		if typBodu == CON:
			zapisAtribut(element, "adj", souradnice[typSouradnic].upper())

# nacteni bodu a zapis souradnic
sys.stderr.write("Souradnice vlozene do souboru: ")
Ebody = dom.getElementsByTagName('point')
for Ebod in Ebody:
	if Ebod.nodeType == 1: # Element
		if Ebod.attributes:
			attr = Ebod.attributes.getNamedItem("id")
			pointId = attr.value
			id_nalezeno=0
			for id in sour:
				if id == pointId:
					id_nalezeno=1
					# zapis souradnic
					zapisAtribut(Ebod, "x", sour[id][0], force)
					zapisAtribut(Ebod, "y", sour[id][1], force)
					if filetype == XYZ or filetype == YXZ:
						zapisAtribut(Ebod, "z", sour[id][2], force)
					# zapis typu bodu - atribut adj nebo fix
					zapisTypBodu(Ebod, typBodu, filetype, force)
					# vypis doplnenych bodu
					if filetype == XY:
						sys.stderr.write("%s(XY) " % id)
					if filetype == YX:
						sys.stderr.write("%s(YX) " % id)
					if filetype == XYZ:
						sys.stderr.write("%s(XYZ) " % id)
					if filetype == YXZ:
						sys.stderr.write("%s(YXZ) " % id)
			if id_nalezeno == 0:
				zapisTypBodu(Ebod, ADJ, filetype, force)
sys.stderr.write("\n")

# vypsani doplneneho XML stromu
sys.stdout.write(dom.toxml())
