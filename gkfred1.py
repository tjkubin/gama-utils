#!/usr/bin/python

# prevod prostorove site 3D na sit vyskovou 1D
#
# body 3D -> 1D
#
# vypocet prevyseni z merenych sikmych delek a zenitek
# uvazuje se vliv zakriveni Zeme
#
# priklad
#
# ./gkfred1.py < sit.gkf > sit-z.gkf

# Author: Tomas Kubin
# Institute: FSv, CVUT v Praze, Katedra geodezie a pozemkovych uprav
# License: GPL

import sys
import math

R = 6380e3

# nacteni DOM
from xml.dom import minidom
dom = minidom.parse(sys.stdin);

# zmena parametru tagu <point>
Epoints = dom.getElementsByTagName('point')
pbodu = 0 # pocet nactenych bodu
for ep in Epoints:
	fix = ep.attributes.getNamedItem('fix')
	adj = ep.attributes.getNamedItem('adj')

	# odstraneni bodu typu xy
	if fix and fix.value.lower() == "xy":
		ep.removeAttribute('fix')
		#ep.unlink()
	if adj and adj.value.lower() == "xy":
		ep.removeAttribute('adj')
		#ep.unlink()

	# odstraneni souradnice x,y u bodu typu xyz
	if fix and fix.value.lower() == "xyz":
		ep.removeAttribute('fix')
		ep.setAttribute('fix','z')
	if adj and adj.value.lower() == "xyz":
		ep.removeAttribute('adj')
		ep.setAttribute('adj',adj.value[2])

# nacteni presnosti
epointsObs = dom.getElementsByTagName('points-observations')[0]
dist_stdev = epointsObs.getAttribute("distance-stdev")
zen_stdev = epointsObs.getAttribute("zenith-angle-stdev")
zen_stdev = float(zen_stdev)
zen_stdev *= 1e-4 * math.pi / 200 # prevod cc -> radiany
abc = dist_stdev.split(" ")

# vypocet prevyseni
Eobs = dom.getElementsByTagName('obs')
for eo in Eobs:
	stn = eo.attributes.getNamedItem('from').value # id stanoviska
	Edist = eo.getElementsByTagName('s-distance') # sikme delky
	Ezen  = eo.getElementsByTagName('z-angle') # zenitove uhly
	# novy tag <height-differences>
	ehd = dom.createElement("height-differences")
	epointsObs.appendChild(ehd)
	for ed in Edist: # prochazi sikme delky
		to = ed.attributes.getNamedItem("to").value # id sikme delky
		sdist = float(ed.attributes.getNamedItem("val").value) # sikma delka
		# vyhledani zenitoveho uhlu podle to delky
		ez = None
		for e in Ezen:
			if e.attributes.getNamedItem("to").value == to:
				ez = e
				break
		if ez==None:
			sys.stderr.write("no <z-angle> for  <s-distance from=\"%s\" to=\"%s\"/>\n" %(stn,id))
			sys.stderr.write("height difference not computed\n")
			#eo.removeChild(ed) # odstraneni sikme delky
			continue
		# vypocet prevyseni
		zen=float(ez.attributes.getNamedItem("val").value)
		dist = sdist * math.sin(zen*math.pi/200)
		phi2 = dist/2/R # phi2 polovina geocentrickeho uhlu
		dh = sdist * math.cos(zen*math.pi/200 - phi2) / math.cos(phi2)
		# vypocet presnosti prevyseni
		if len(abc) == 1 : 
			dist_stdev = float(abc[0])
		if len(abc) == 2 : 
			dist_stdev = float(abc[0]) + sdist*float(abc[1])
		if len(abc) == 3 : 
			dist_stdev = float(abc[0]) + sdist*1e-3*float(abc[1])**float(abc[2])
		dist_stdev *= 1e-3 # prevod mm -> m
		dh_stdev = math.sqrt(
			sdist**2*math.sin(zen*math.pi/200)**2*zen_stdev**2 + 
			math.cos(zen*math.pi/200)**2*dist_stdev**2 )
		dh_stdev *= 1e3 # prevod m -> mm

		# vytvoreni tagu dh
		edh = dom.createElement("dh");
		edh.setAttribute('from', "%s" % stn)
		edh.setAttribute('to', "%s" % to)
		edh.setAttribute('val', "%.4f" % dh)
		if dh_stdev < 0.1: # zajisteni alespon dvou platnych cifer
			edh.setAttribute('stdev', "%.2e" % dh_stdev)
		else:
			edh.setAttribute('stdev', "%.2f" % dh_stdev)
		ehd.appendChild(edh)
	epointsObs.removeChild(eo)


# vypsani upraveneho XML stromu
sys.stdout.write(dom.toxml())
