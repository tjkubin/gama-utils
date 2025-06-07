import io
from contextlib import redirect_stdout
from gamaxml2txt import gamaXMLParser


def test_parse_adj_xml_first_line():
    parser = gamaXMLParser()
    out = io.StringIO()
    with open('examples/adj.xml', 'rb') as f, redirect_stdout(out):
        parser.parse_file(f)
    first_line = out.getvalue().splitlines()[0]
    assert first_line == "9701 486568.551000 5377832.049000 290.700000 #xyz_fix"
