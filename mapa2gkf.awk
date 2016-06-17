#!/usr/bin/awk -f

# konverze formatu MAPA 2 do souboru GKF (vstup pro vyrovnani v gama-local)
#
# MAPA 2
#
# sloupec	popis
#-------------------------------
# mereni:
#	1	cislo bodu
#	2	typ delky
#	3	delka
#	4	vyska cile
#	5	vodorovny smer
#	6	zenitovy uhel
# stanovisko:
#	1	1
#	2	cislo stanoviska
#	3	vyska stroje
#
# Priklad pouziti
#
# ./mapa2gkf.awk -v dir=20 dist="5 3" vstupni_soubor_mereni
#
# dir  ... presnost merenych smeru a zenitek ve vterinach
# dist ... presnost merenych delek a[mm] + b[mm/km]


# Author: Tomas Kubin
# Institute: FSv, CVUT v Praze, Katedra geodezie a pozemkovych uprav
# License: GPL

BEGIN {
	version="1.0"
	if (dir==0) dir=10
	if (dist==0) dist="2 2 1"
	print "<?xml version=\"1.0\"?>"
	print "<!DOCTYPE gama-xml SYSTEM \"http://www.gnu.org/software/gama/gama-xml.dtd\">"
	print "\n<gama-local>"
	print "<network axes-xy=\"en\" angles=\"left-handed\">"
	print "<parameters"
	print "  sigma-apr = \"1.00\""
	print "  conf-pr   = \"0.95\""
	print "  sigma-act = \"apriori\""
	print "  update-constrained-coordinates = \"no\"/>"
	first_file=1 # je to prvni soubor?
	block_points_obs=0 # indikator bloku <points-observations>
	block_descr=0 # indikator bloku popisu
	stn=null # id stanoviska
	done=0 # ukazatel zda byl radek uz zpracovan
  error=0 # indikator chyboveho stavu
	# kdyz nebyl radek zpracovan vypise se poslednim pravidlem chyba
}

FNR==1 { # vypsani jmena souboru
	printf("Soubor: %s\n", FILENAME) > "/dev/stderr"
	if(FNR != NR) first_file=0 # je zpracovavan prvni soubor
	block_obs=0 # indikator bloku stanoviska
}

/^ *$/ { next } # prazdny radek 

/^ *[#%]/ { next } # komentar 

/^\// { next } # oddeleni stanovisek - nepouziva se

/^;/ && first_file=1{ # hlavicka souboru se ulozi do tagu <description>
	done=1
	if (block_descr == 0) print "<description>"
	block_descr = 1;
	print $2
}

$1==1 && NF==3 { # udaje o stanovisku
	done=1
	# popis
	if(first_file==1 && stn==null) { # jen u prvniho souboru pred prvnim stn
		if(block_descr==0) print "<description>" 
		print  "----"
		printf("Soubor: %s\n", FILENAME)
		printf("Dne: %s\n", strftime("%Y-%m-%d, %H:%M %Z"))
		printf("Generovano programem mapa2gkf.awk (ver. %s)\n", version)
		print  "</description>"
	}
	if(block_points_obs==0) { # zacatek tagu <points-observations>
		print  "<points-observations"
		printf("  direction-stdev=\"%i\"\n", dir)
		printf("  zenith-angle-stdev=\"%i\"\n", dir)
		printf("  distance-stdev = \"%s\">\n", dist)
		block_points_obs=1
	}
	if(block_obs == 1) print "  </obs>" # uzavreni stanoviska

	# stanovisko - uvodni tag <obs>
	print "  <obs from = \"" $2 "\" from_dh = \"" $3 "\">"
	if ($3+0.0 == 0.0) 
		printf("%i(%s):(varovani) nulova vyska stroje\n", FNR, $2) > "/dev/stderr"
	block_obs = 1
	stn = $2
	body[NR] = $2
}

NF==6 && block_obs==1 { # mereni
	done=1
	if ($4+0.0 == 0.0)
		printf("%i(%s->%s):(varovani) nulova vyska cile\n", FNR, stn, $1) > "/dev/stderr"
	# smery
	print "    <direction to = \"" $1 \
	      "\" val = \"" $5 \
	      "\" to_dh = \"" $4 \
	      "\"/>"
	#if ($2 == "2") { # sikme delky
		if ($3+0.0 == 0.0) { # nulova delka
			printf("%i(%s->%s): smer bez delky - nulova delka\n", FNR, stn, $1) > "/dev/stderr"
		}else{
			print "    <s-distance to = \"" $1 \
		              "\" val = \"" $3 \
			      "\" to_dh = \"" $4 \
			      "\"/>"
	        }
	#}else{
  #     		printf("%i(%s->%s): delka neni sikma - kod %i (nezpracovano)\n", FNR, stn, $1, $2) > "/dev/stderr"}
	# zenitovy uhel
  if ($6+0.0 > 200) {
    printf("%i(%s->%s): Error: zenith angle greater than 200 gon\n", FNR, stn, $1) > "/dev/stderr"
    error = 1
    exit 1
  }
  print "    <z-angle to = \"" $1 \
        "\" val = \"" $6 \
        "\" to_dh = \"" $4 \
        "\"/>"
	body[NR] = $1
}

/^-2/ { done=1 } # konec souboru

/.*/ { # odchytavani nezpracovanych radku
	if (done==0)
		printf("%i(nezpracovany radek): %s\n", FNR, $0) > "/dev/stderr"
	done=0
}

END {	# uzavreni tagu </obs>
  if(error!=0) {
    exit 1
  }

	if(block_obs == 1) print "  </obs>"
	
	# vypis bodu bez opakovani	
	asort(body)
	for (i in body){
		if(body[i]==body[i+1]){
			continue; 
		}else{
			print "  <point id = \"" body[i] "\"/>";
		}
	}
	
	# ukonceni XML
	if(block_points_obs==1) print "</points-observations>"
	print "</network>"
	print "</gama-local>"
}
