#!/usr/bin/python

'''
coordinate, precision, covariance matrix export from gama-local-adjustment

usage: ./gamaxml2txt.py < adjustment.xml > coordinates.txt
usage: ./gamaxml2txt.py --covmat covMatFile.txt < adjustment.xml > coordinates.txt
'''

## Author: Tomas Kubin
## License: GPL

from __future__ import print_function
import sys
import xml.parsers.expat


class gamaXMLParserError(Exception):
    'Exception for gamaXMLParser'
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class gamaXMLParser:
    '''Expat parser for gamaXMLParser 1.0 document'''

    def __init__(self):
        # create expat parser
        self.__parser = xml.parsers.expat.ParserCreate()
        self.__parser.StartElementHandler = self.__handle_start_element
        self.__parser.EndElementHandler = self.__handle_end_element
        self.__parser.CharacterDataHandler = self.__handle_char_data

        # internal data
        self.__characterData = ""
        self.__attrs = []
        self.__type = "#"
        self.__readPoint = False  # read tag <point> ?
        self.__isFix = False  # section <fixed>
        self.__covmat = [] # covariance matrix

    def parse_file(self, file):
        '''parses file - file object'''
        self.__parser.ParseFile(file)

    def __handle_start_element(self, name, attrs):
        '''start element handler'''
        if name == "adjusted":
            self.__readPoint = True
            self.__characterData = ""
            self.__type = "#"
            self.__attrs = []
        elif name == "fixed":
            self.__readPoint = True
            self.__isFix = True
            self.__characterData = ""
        elif name == "point":
            self.__characterData = ""
        elif name == "cov-mat":
            self.__characterData = ""

    def __handle_end_element(self, name):
        '''end element handler'''

        if name == "id":
            self.__attrs.append(self.__characterData.strip())
            self.__characterData = ""
        elif name == "x" or name == "y" or name == "z" or\
             name == "X" or name == "Y" or name == "Z":
            self.__attrs.append(self.__characterData.strip())
            self.__characterData = ""
            self.__type += name
        elif name == "point" and self.__readPoint is True:
            if self.__isFix:
                self.__type += "_fix"
            self.__attrs.append(self.__type)
            if len(self.__attrs) > 2:
                print(" ".join(self.__attrs))
            self.__type = "#"
            self.__attrs = []
        elif name == "fixed":
            self.__readPoint = False
            self.__isFix = False
        elif name == "dim":
            self.__dim = int(self.__characterData.strip())
            self.__characterData = ""
        elif name == "band":
            self.__band = int(self.__characterData.strip())
            self.__characterData = ""
        elif name == "flt":
            self.__covmat.append(self.__characterData.strip())
            self.__characterData = ""

    def __handle_char_data(self, data):
        '''character data handler for method all and info'''
        self.__characterData += data

    def write_cov_mat(self, file):
        dim = self.__dim
        band = self.__band
        #num = (dim + 1) * dim / 2 - (dim - band) * (dim - band - 1) / 2
        ll = []  # list of rows of upper triangular part of covariance matrix
        ll.append([])
        radek = 0
        sloupec = 0
        for val in self.__covmat:
            if sloupec - radek > band or sloupec > dim - 1:
                ll.append([])
                radek = radek + 1
                sloupec = radek
            ll[radek].append(val)
            sloupec = sloupec + 1
        for row in xrange(dim):
            for col in xrange(dim):
                if abs(col-row) > band:
                    print(" 0.0          ", file=file, end='')
                    continue
                if col < row:
                    print(' ', file=file, end='')
                    print(ll[col][row-col], file=file, end='')
                else:
                    print(' ', file=file, end='')
                    print(ll[row][col-row], file=file, end='')
                #print((row, col), file=sys.stderr)
            print('', file=file)

if __name__ == "__main__":

    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("", "--covmat", dest="covmatFile",
            help="Covariance matrix output to a FILE")
    (options, args) = parser.parse_args()
    parser = gamaXMLParser()
    parser.parse_file(sys.stdin)
    if options.covmatFile is not None:
        try:
            cfile = open(options.covmatFile, 'wt')
            #print("Opening file %s" % options.covmatFile)
        except Exception:
            sys.exit('Cant open file %s for writing' % options.covmatFile)
        parser.write_cov_mat(cfile)
        cfile.close()
