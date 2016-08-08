from xd import etree
from StringIO import StringIO

TESTXML = """<?xml version="1.0"?>
<note
xmlns="http://www.w3schools.com"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.w3schools.com note.xsd">
  <to>Tove</to>
  <from>Jani</from>
  <heading>Reminder</heading>
  <body>Don't forget me this weekend!</body>
</note>
"""

def test_qualified():
    assert etree.qualified('{http://www.examle.com/}foo')
    assert not etree.qualified('xsi:foo')
    assert not etree.qualified('foo')

def test_prefixed():
    assert  etree.prefixed('xsi:foo')
    assert not etree.prefixed('{http://www.examle.com/}foo')
    assert not etree.prefixed('foo')

def test_fromstring():
    e = etree.fromstring(TESTXML)
    assert isinstance(e, etree.BaseElm)

def test_parse():
    e = etree.parse(StringIO(TESTXML))
    assert isinstance(e, etree.ET._ElementTree)

