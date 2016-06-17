#!/usr/bin/python

# prevod prostorove site 3D na sit polohovou 2D
#
# body 3D -> 2D
#
# redukce sikmych delek na vodorovnou, do nuloveho horizontu a do zobrazeni
# s-distance, z-angle -> distance 
#
# priklad pouziti
# ./gkfred2.py < sit.gkf > sit-xy.gkf
#	redukce delek z nadmorsle vysky a zobrazeni 
#	podle souradnic bodu v XML souboru sit.gkf
#
# ./gkfred2.py --height=250 --jtskxy=1100100,650100 < sit.gkf > sit-xy.gkf
#	redukce delek podle zadane nadmorske vysky a souradnic
#
# ./gkfred2.py --ppm=-100 < sit.gkf > sit-xy.gkf
#	redukce delek podle meritka v jednotkach mm/km

# Author: Tomas Kubin
# Institute: FSv, CVUT v Praze, Katedra geodezie a pozemkovych uprav
# License: GPL

import sys
import math

R = 6380e3

# nacteni vstupnich parametru
from optparse import OptionParser
parser = OptionParser()
parser.add_option("", "--height", action="store", type="float", dest="height",
		help="nadmorska vyska pro redukci")
parser.add_option("", "--jtskxy", action="store", dest="jtskxy", 
		help="redukce delek ze zobrazeni do S-JTSK = souradnice_x,souradnice_y")
parser.add_option("", "--ppm", action="store", type="float", dest="ppm",
		help="celkova redukce delek v mm/km")
#parser.add_option("", "--m", action="store", type="float", dest="meritko_m",
#		help="meritko redukce delek - neimplementovano")
(options, args) = parser.parse_args();

# redukce
ppm = None # celkova redukce
ppm_h = None # redukce z nadmorske vysky
ppm_k = None # redukce z Krovakova zobrazeni
jtskx=None; jtsky=None; jtskz=0 # souradnice pro redukce

# volba --ppm
if options.ppm:
	ppm = options.ppm
	sys.stderr.write("Celkova redukce: %.1f ppm\n" % ppm)

# volba --height
if options.height and not ppm:
	jtskz=options.height

# volba --jtskxy
if options.jtskxy and not ppm:
	jtskxy=options.jtskxy.split(',')
	if len(jtskxy) != 2:
		exit("Chybna hodnota prepinace: --jtskxy=souradnice_x,souradnice_y")
	jtskx=float(jtskxy[0])
	jtsky=float(jtskxy[1])

# nacteni DOM
from xml.dom import minidom
dom = minidom.parse(sys.stdin);

# nacteni souradnic <point> a uprava atributu
Epoints = dom.getElementsByTagName('point')
numx=0; numy=0; numz=0 # pocet nactenych souradnic x, y, z
jtskx_=0; jtsky_=0; jtskz_=0 # prumerovane souradnice
for ep in Epoints:
	if not ppm: 
		# nacteni a zprumerovani souradnic x y a z
		atts = ep.attributes #NamedNodeMap
		for i in range(atts.length):
			att = atts.item(i) # attribute node
			if att.nodeName.lower() == 'x':
				x = float(att.nodeValue)
				jtskx_ = (numx*jtskx_ + x) / (numx + 1)
				numx+=1
			if att.nodeName.lower() == 'y':
				y = float(att.nodeValue)
				jtsky_ = (numy*jtsky_ + y) / (numy + 1)
				numy+=1
			if att.nodeName.lower() == 'z':
				z = float(att.nodeValue)
				jtskz_ = (numz*jtskz_ + z) / (numz + 1)
				numz+=1
	
	# odstraneni souradnice z
	if ep.attributes.getNamedItem('z'):
		ep.removeAttribute('z')
	# 'xyz' -> 'xy' u atributu 'fix'
	fix = ep.attributes.getNamedItem('fix')
	if fix and fix.value.lower() == "xyz":
		ep.removeAttribute('fix')
		ep.setAttribute('fix','xy')
	# 'xyz' -> 'xy' u atributu 'adj'
	adj = ep.attributes.getNamedItem('adj')
	if adj and adj.value.lower() == "xyz":
		val = adj.value
		ep.removeAttribute('adj')
		ep.setAttribute('adj',val[:2])

if not ppm:
	# ulozeni prumernych souradnic
	if not jtskx: 
		jtskx = jtskx_
		sys.stderr.write("Souradnice x: %.3f\n" % jtskx)
	if not jtsky: 
		jtsky = jtsky_
		sys.stderr.write("Souradnice y: %.3f\n" % jtsky)
	if not jtskz: 
		jtskz = jtskz_
		sys.stderr.write("Souradnice z: %.3f\n" % jtskz)

	# varovani pri nulovych souradnicich
	if jtskx == 0: sys.stderr.write("Pozor: x-ova souradnice pro redukci je nulova\n")
	if jtsky == 0: sys.stderr.write("Pozor: y-ova souradnice pro redukci je nulova\n")
	if jtskz == 0: sys.stderr.write("Pozor: vyska pro redukci je nulova\n")

	# redukce z nadmorske vysky
	ppm_h = -1e6 * jtskz / R
	sys.stderr.write("Redukce z nadmorske vysky: %.1f ppm\n" % ppm_h) 
			
	# redukce ze zobrazeni
	r  = math.sqrt(jtskx**2 + jtsky**2)
	r0 = 1298039.0046 # v metrech
	dr = (r - r0)*1e-5 # dr - ve stovkach km
	ppm_k = -100 + 122.82*dr**2 - 3.15*dr**3 + 0.18*dr**4
	sys.stderr.write("Redukce ze zobrazeni: %.1f ppm\n" % ppm_k) 
	
	# celkova redukce
	ppm = ppm_h + ppm_k
	sys.stderr.write("Celkova redukce: %.1f ppm\n" % ppm)


# redukce mereni v jednotlivych osnovach
Eobs = dom.getElementsByTagName('obs')
for eo in Eobs: # prochazi stanoviska
	stn = eo.attributes.getNamedItem('from').value # id stanoviska
	Edist = eo.getElementsByTagName('s-distance') # sikme delky
	Ezen  = eo.getElementsByTagName('z-angle') # zenitove uhly
	for ed in Edist: # prochazi sikme delky
		to = ed.attributes.getNamedItem("to").value # id sikme delky
		sdist = float(ed.attributes.getNamedItem("val").value) # sikma delka
		# vyhledani zenitoveho uhlu podle id
		ez = None
		for e in Ezen:
			if e.attributes.getNamedItem("to").value == to:
				ez = e
				break
		if ez==None:
			sys.stderr.write("z-angle is missing\n")
			sys.stderr.write("deleting <s-distance from=\"%s\" to=\"%s\"/>\n" %(stn,id))
			eo.removeChild(ed) # odstraneni sikme delky
			continue
		# redukce na vodorovnou
		zen=float(ez.attributes.getNamedItem("val").value)
		dist = sdist * math.sin(zen*math.pi/200)
		# redukce do S-JTSK (nadmorska vyska, zobrazeni)
		dist *= (1 + ppm*1e-6)
		# vlozeni redukovane delky <distance>
		edist = dom.createElement('distance')
		edist.setAttribute('to', to)
		edist.setAttribute('val', "%.5f" % dist)
		eo.appendChild(edist)
		# vymazani sikme delky <s-distance> a zenitoveho uhlu <z-angle>
		eo.removeChild(ed)
		eo.removeChild(ez)
	# odstraneni atributu from_dh z tagu <obs>
	eo.removeAttribute('from_dh')
	# odstraneni atributu to_dh z tagu <direction>
	Edir  = eo.getElementsByTagName('direction') # smery
	for ed in Edir:
		ed.removeAttribute('to_dh')
	# odstraneni zenitovych uhlu na body bez delky
	Ezen  = eo.getElementsByTagName('z-angle') # zenitove uhly
	for ez in Ezen:
		eo.removeChild(ez)

# vypsani doplneneho XML stromu
#sys.stdout.write(dom.toprettyxml())
sys.stdout.write(dom.toxml())
