from xd.builtins import *

def test_length():
    facet = length(3)
    assert not facet('fo')
    assert facet('foo')
    assert not facet('fooo')

def test_maxlength():
    facet = maxlength(3)
    assert facet('fo')
    assert facet('foo')
    assert not facet('fooo')

def test_minlength():
    facet = minlength(3)
    assert not facet('fo')
    assert facet('foo')
    assert facet('fooo')

def test_pattern():
    facet = pattern("[A-Z]{2}\d\s\d[A-Z]{2}")
    assert facet('FO3 1FD')
    assert not facet('FOA FD2')

def test_enumeration():
    facet = enumeration('foo')
    facet.restriction.append('bar')
    assert facet('foo')
    assert facet('bar')
    assert not facet('bang')

def test_whitespace():
    facet = whitespace('preserve')
    assert ' foo \n\r\t' == facet(' foo \n\r\t')
    facet = whitespace('replace')
    assert ' foo    ' == facet(' foo \n\r\t'), facet(' foo \n\r\t')
    facet = whitespace('colapse')
    assert ' foo ' == facet(' foo \n\r\t')

def test_totaldigits():
    facet = totaldigits(3)
    assert facet(1)
    assert facet(12)
    assert facet(123)
    assert facet(999)
    assert not facet(1000)
    assert not facet(1234)
    assert not facet(12345)
