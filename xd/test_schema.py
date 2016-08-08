from datetime import datetime
from xd.schema import Schema
from xd import etree

def datafile(path):
    return 'testdata/{0}'.format(path)

TESTXSD = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
targetNamespace="http://www.w3schools.com"
xmlns="http://www.w3schools.com"
elementFormDefault="qualified">

<xs:element name="note">
<xs:complexType>
<xs:sequence>
  <xs:element name="to" type="xs:string"/>
  <xs:element name="from" type="xs:string"/>
  <xs:element name="heading" type="xs:string"/>
  <xs:element name="body" type="xs:string"/>
</xs:sequence>
</xs:complexType>
</xs:element>

</xs:schema>
"""

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

TESTXSD1 = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
targetNamespace="http://www.w3schools.com"
xmlns="http://www.w3schools.com"
elementFormDefault="qualified">

<xs:element name="note">
<xs:complexType>
<xs:sequence>
  <xs:element name="to" type="xs:string"/>
  <xs:element name="from" type="xs:string"/>
  <xs:element name="heading" type="xs:string"/>
  <xs:element name="body" type="xs:string"/>
</xs:sequence>
<xs:attribute name="testAttr" type="xs:string"/>
</xs:complexType>
</xs:element>

</xs:schema>
"""

TESTXML1 = """<?xml version="1.0"?>
<note
xmlns="http://www.w3schools.com"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.w3schools.com note.xsd"
testAttr="foo">
  <to>Tove</to>
  <from>Jani</from>
  <heading>Reminder</heading>
  <body>Don't forget me this weekend!</body>
</note>
"""

TESTXSD2 = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
targetNamespace="http://www.w3schools.com"
xmlns="http://www.w3schools.com"
elementFormDefault="qualified">

<xs:element name="note">
<xs:complexType>
<xs:sequence>
  <xs:element name="body" type="xs:string"/>
</xs:sequence>
<xs:attribute name="testAttr" type="xs:integer"/>
</xs:complexType>
</xs:element>

</xs:schema>
"""

TESTXML2 = """<?xml version="1.0"?>
<note
xmlns="http://www.w3schools.com"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.w3schools.com note.xsd"
testAttr="4">
  <body>Don't forget me this weekend!</body>
</note>
"""

TESTXSD3 = """
<element name="note" xmlns="http://www.w3.org/2001/XMLSchema">
<complexType>
<sequence>
  <element name="body" type="string"/>
</sequence>
<attribute name="testAttr" type="integer"/>
</complexType>
</element>
"""

TESTXML3 = """
<note
testAttr="4">
  <body>Don't forget me this weekend!</body>
</note>
"""

#schema = Schema()
#et = etree.fromstring(TESTXSD)
#parse = Parser(schema, handlers)
#parse(et)
#et = etree.fromstring(TESTXML)
#note = instance(et, schema)

def test_schema():
    """
    schema obj gen
    """
    schema = Schema()
    et = etree.fromstring(TESTXSD)
    schema.parse(et)
    et = etree.fromstring(TESTXML)
    note = schema.instance(et)
    assert note.to == "Tove"
    assert note.frm == "Jani"
    assert note.heading == "Reminder"
    assert note.body == "Don't forget me this weekend!"


def test_schema1():
    """
    schema obj w/ string attribute
    """
    schema = Schema()
    et = etree.fromstring(TESTXSD1)
    schema.parse(et)
    et = etree.fromstring(TESTXML1)
    note = schema.instance(et)
    assert note.to == "Tove"
    assert note.frm == "Jani"
    assert note.heading == "Reminder"
    assert note.body == "Don't forget me this weekend!"
    assert note.testAttr == 'foo'


def test_schema2():
    """
    schema obj w/ integer attribute
    """
    schema = Schema()
    et = etree.fromstring(TESTXSD2)
    schema.parse(et)
    et = etree.fromstring(TESTXML2)
    note = schema.instance(et)
    assert note.body == "Don't forget me this weekend!"
    assert note.testAttr == 4, note.testAttr

def test_schema3():
    """
    schema minimal
    """
    # Schema without full document and namespaces
    schema = Schema()
    et = etree.fromstring(TESTXSD3)
    schema.parse(et)
    et = etree.fromstring(TESTXML3)
    note = schema.instance(et)
    assert note.body == "Don't forget me this weekend!"
    assert note.testAttr == 4, note.testAttr

def test_schema4():
    """
    test schema full example
    """
    schema = Schema()
    et = etree.frompath(datafile('po.xsd'))
    schema.parse(et)
    et = etree.frompath(datafile('po.xml'))
    purchaseOrder = schema.instance(et)
    assert purchaseOrder.billTo.zip == 95819
    assert purchaseOrder.billTo.name == "Robert Smith", \
        purchaseOrder.billTo.name
    assert purchaseOrder.comment == "Hurry, my lawn is going wild"
    assert purchaseOrder.orderDate == datetime(1999, 10, 20, 0, 0)
    for item in purchaseOrder.items:
        assert item.partNum in ['872-AA', '926-AA']
        if item.partNum == '872-AA':
            assert item.productName == 'Lawnmower', item.productName
            assert item.quantity == 1, item.quantity
            assert item.USPrice == 148.95, item.USPrice
            assert item.comment == 'Confirm this is electric', item.comment
            assert item.shipDate == None, item.shipDate
        elif item.partNum == '926-AA':
            assert item.productName == 'Baby Monitor', item.productName
            assert item.quantity == 1, item.quantity
            assert item.USPrice == 39.98, item.USPrice
            assert item.comment == None, item.comment
            assert item.shipDate == datetime(1999, 5, 21), item.shipDate

def test_schema_ipo1_1():
    """
    """
    schema = Schema()
    et = etree.frompath(datafile('ipo1/ipo.xsd'))
    schema.parse(et)
    et = etree.frompath(datafile('ipo1/ipo_1.xml'))
    purchaseOrder = schema.instance(et)
    assert purchaseOrder.orderDate == datetime(2002,10,20), \
        purchaseOrder.orderDate
    assert purchaseOrder.shipTo.name == 'Alice Smith', \
        purchaseOrder.shipTo.name
    assert purchaseOrder.shipTo.street == '123 Maple Street', \
        purchaseOrder.shipTo.street
    assert purchaseOrder.shipTo.city == 'Mill Valley', \
        purchaseOrder.shipTo.city
    assert purchaseOrder.shipTo.state == 'AL', \
        purchaseOrder.shipTo.state
    assert purchaseOrder.shipTo.zip == 90952, \
        purchaseOrder.shipTo.zip
    assert purchaseOrder.billTo.name == 'Robert Smith', \
        purchaseOrder.billTo.name
    assert purchaseOrder.billTo.street == '8 Oak Avenue', \
        purchaseOrder.billTo.street
    assert purchaseOrder.billTo.city == 'Old Town', \
        purchaseOrder.billTo.city
    assert purchaseOrder.billTo.state == 'AK', \
        purchaseOrder.billTo.state
    assert purchaseOrder.billTo.zip == 95800, \
        purchaseOrder.billTo.zip
    assert purchaseOrder.comment == 'Hurry, my sister loves Boeing!', \
        purchaseOrder.comment
    for item in purchaseOrder.items:
        assert item.partNum in ['777-BA', '833-AA']
        if item.partNum == '777-BA':
            assert item.weightKg == 4.5
            assert item.shipBy == 'land'
            assert item.productName == '777 Model'
            assert item.quantity == 1
            assert item.USPrice == 99.95
            for comment in item.comment:
                assert comment in [
                    ' Use gold wrap if possible ',
                    ' Want this for the holidays! '
                ], comment
            assert item.shipDate == datetime(1999,12,5)
        if item.partNum == '833-AA':
            assert item.weightKg == None
            assert item.shipBy == None
            assert item.productName == '833 Model'
            assert item.quantity == 2, item.quantity
            assert item.USPrice == 199.95
            assert item.shipDate == datetime(2000,2,28)

def test_schema_ipo1_2():
    """
    """
    schema = Schema()
    et = etree.frompath(datafile('ipo1/ipo.xsd'))
    schema.parse(et)
    et = etree.frompath(datafile('ipo1/ipo_2.xml'))
    purchaseOrder = schema.instance(et)
    assert purchaseOrder.orderDate == datetime(2002,10,20), \
        purchaseOrder.orderDate
    assert purchaseOrder.singleAddress.name == 'Helen Zoe'
    assert purchaseOrder.singleAddress.street == '47 Eden Street'
    assert purchaseOrder.singleAddress.city == 'Cambridge'
    assert purchaseOrder.singleAddress.postcode == 'CB1 1JR'
    assert purchaseOrder.singleAddress.exportCode == 1
    assert purchaseOrder.comment == 'I love Boeing too!'
    for item in purchaseOrder.items:
        assert item.partNum in ['777-BA', '833-AA']
        if item.partNum == '777-BA':
            assert item.weightKg == 4.5
            assert item.shipBy == 'any'
            assert item.quantity == 1
            assert item.productName == '777 Model'
            assert item.USPrice == 99.95
            assert item.shipDate == datetime(1999,12,5)
        if item.partNum == '833-AA':
            assert item.weightKg == None
            assert item.shipBy == None
            assert item.productName == '833 Model'
            assert item.quantity == 1
            assert item.USPrice == 199.95
            assert item.shipDate == datetime(2000,2,28)


def validate_ipo2_1(purchaseOrder):
    assert purchaseOrder.orderDate == datetime(2002,10,20), \
        purchaseOrder.orderDate
    assert purchaseOrder.shipTo.name == 'Alice Smith', \
        purchaseOrder.shipTo.name
    assert purchaseOrder.shipTo.street == '123 Maple Street', \
        purchaseOrder.shipTo.street
    assert purchaseOrder.shipTo.city == 'Mill Valley', \
        purchaseOrder.shipTo.city
    assert purchaseOrder.shipTo.state == 'CA', \
        purchaseOrder.shipTo.state
    assert purchaseOrder.shipTo.zip == 90952, \
        purchaseOrder.shipTo.zip
    assert purchaseOrder.billTo.name == 'Robert Smith', \
        purchaseOrder.billTo.name
    assert purchaseOrder.billTo.street == '8 Oak Avenue', \
        purchaseOrder.billTo.street
    assert purchaseOrder.billTo.city == 'Old Town', \
        purchaseOrder.billTo.city
    assert purchaseOrder.billTo.state == 'PA', \
        purchaseOrder.billTo.state
    assert purchaseOrder.billTo.zip == 95819, \
        purchaseOrder.billTo.zip
    assert purchaseOrder.comment == 'Hurry, my sister loves Boeing!', \
        purchaseOrder.comment
    for item in purchaseOrder.items:
        assert item.partNum in ['777-BA', '833-AA']
        if item.partNum == '777-BA':
            assert item.weightKg == 4.5
            assert item.shipBy == 'air'
            assert item.productName == '777 Model'
            assert item.quantity == 1
            assert item.USPrice == 99.95
            for comment in item.comment:
                assert comment in [
                    ' Use gold wrap if possible ',
                    ' Want this for the holidays! '
                ], comment
            assert item.shipDate == datetime(1999,12,5)
        if item.partNum == '833-AA':
            assert item.weightKg == 2.5
            assert item.shipBy == 'air'
            assert item.productName == '833 Model'
            assert item.quantity == 2, item.quantity
            assert item.USPrice == 199.95
            assert item.shipDate == datetime(2000,2,28)

def test_schema_ipo2_1a():
    """
    Can manually add schema documents.
    """
    schema = Schema()
    et = etree.frompath(datafile('ipo2/address.xsd'))
    schema.parse(et)
    et = etree.frompath(datafile('ipo2/ipo.xsd'))
    schema.parse(et)
    et = etree.frompath(datafile('ipo2/ipo_1.xml'))
    purchaseOrder = schema.instance(et)
    validate_ipo2_1(purchaseOrder)

def test_schema_ipo2_1b():
    """
    Document locator locates schema documents in directories where other
    schema docs exist.
    """
    schema = Schema()
    et = etree.frompath(datafile('ipo2/ipo.xsd'))
    schema.parse(et)
    et = etree.frompath(datafile('ipo2/ipo_1.xml'))
    purchaseOrder = schema.instance(et)
    validate_ipo2_1(purchaseOrder)

def test_schema_ipo2_1c():
    """
    Document locator locates schema documents when given a directory.
    """
    schema = Schema(datafile('ipo2/'))
    et = etree.frompath(datafile('ipo2/ipo_1.xml'))
    purchaseOrder = schema.instance(et)
    validate_ipo2_1(purchaseOrder)

def test_schema_ipo2_1d():
    """
    Document locator locates schema documents form xml document
    directory
    """
    schema = Schema()
    et = etree.frompath(datafile('ipo2/ipo_1.xml'))
    purchaseOrder = schema.instance(et)
    validate_ipo2_1(purchaseOrder)

if __name__ == '__main__':
    schema = Schema()
    et = etree.frompath(datafile('ipo2/address.xsd'))
    schema.parse(et)
    et = etree.frompath(datafile('ipo2/ipo.xsd'))
    schema.parse(et)
    et = etree.frompath(datafile('ipo2/ipo_1.xml'))
    purchaseOrder = schema.instance(et)
