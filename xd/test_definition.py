from xd.definition import SimpleTypeDef, AttributeGroupDef, AttributeDec
from xd.builtins import *

def test_simple_type_def():
    decimal = SimpleTypeDef(
        name='decimal',
        basedef=anySimpleType,
        primative=primative.decimal,
    )
    decimal._validfacets = [
        totaldigits.name, fractiondigits.name, pattern.name, whitespace.name,
        enumeration.name, maxinclusive.name, maxexclusive.name,
        mininclusive.name, minexclusive.name,
    ]
    integer = SimpleTypeDef(
        name='integer',
        basedef=decimal,
    )
    integer._validfacets = [
        totaldigits.name, fractiondigits.name, pattern.name, whitespace.name,
        enumeration.name, maxinclusive.name, maxexclusive.name,
        mininclusive.name, minexclusive.name,
    ]
    # SimpleTypeDef's primative method is inherited from base
    # definition.
    assert integer.primative == primative.decimal

def test_attribute_group():
    group = AttributeGroupDef('foo')
    assert group.name == 'foo'
    group.targetns = 'bar'
    assert group.targetns == 'bar'
    group.attributes.append(AttributeDec('bang'))
    assert len(group.attributes) == 1


