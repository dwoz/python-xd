from lxml import etree as ET
import os

#QName = ET.QName

def qualified(name):
    """
    Test if a name is qualified or not
    """
    return name.startswith("{http") and "}" in name

def prefixed(name):
    """
    Test if a name is prefixed or not
    """
    return not name.startswith("{http:") and ":" in name

def split_prefixed(s):
    ns, name = None, s
    try:
        ns, name = s.split(':', 1)
    except ValueError:
        pass
    except AttributeError:
        pass
    return ns, name

def split_qualified(s):
    ns, name = None, s
    try:
        ns, name = s.split('}', 1)
    except ValueError:
        pass
    except AttributeError:
        pass
    else:
        ns = ns[1:]
    return ns, name

class QName(object):

    def __init__(self, et, name=None):
        self.et = et
        self.localname = None
        self.namespace = None
        if not name:
            return
        if qualified(name):
            ns, name = split_qualified(name)
            self.namespace, self.localname = split_qualified(name)
        elif prefixed(name):
            prefix, self.localname = split_prefixed(name)
            if prefix in self.et.nsmap:
                self.namespace = self.et.nsmap[prefix]
        else:
            # Treat unqualified names without a prefix as if they have a
            # prefix with the value of None.
            self.localname = name
            if None in self.et.nsmap:
                self.namespace = self.et.nsmap[None]

    def qualified(self):
        return "{{{0}}}{1}".format(
            self.namespace,
            self.localname,
        )

    def prefixed(self):
        for s in self.et.nsmap:
            if s and self.et.nsmap[s] == self.namespace:
                return '{0}:{1}'.format(s, self.localname)
        return self.localname

    def __str__(self):
        return self.qualified()

class BaseElm(ET.ElementBase):
    """
    Basic Element
    """

    @property
    def namespace(self):
        """
        The namespace of this tag
        """
        tag = ET.QName(self.tag)
        if not tag.namespace and self.getparent() is not None:
            return self.getparent().namespace
        return tag.namespace

    @property
    def tagname(self):
        """
        The tag name (without a namespace)
        """
        tag = ET.QName(self.tag)
        return tag.localname

    @tagname.setter
    def tagname(self, name):
        """
        Update the tag name (a tag name without a namesapce).
        """
        self.tag = str(QName(self.namespace, name))

    @property
    def docpath(self):
        """
        The path of this document. Will be None if the doc path is
        unknown which can happen becuase the document was generated from
        a string and not a file and the docpath has not yet been set.
        """
        return self.getroottree().docinfo.URL

    @docpath.setter
    def docpath(self, path):
        self.getroottree().docinfo.URL = path

    @property
    def docfile(self):
        if self.docpath:
            return os.path.split(self.docpath)[-1]

    @property
    def docroot(self):
        if self.docpath:
            a = os.path.split(self.docpath)
            if len(a) > 1:
                return a[0]

def lookup_schema_target_namespace(e):
    """
    For the given BaseSchema element find the target namespace. The
    targetNamespace is that of this element or if not defined it is that
    of the first parent element which has targetNamespace attribute
    defined.
    """
    if 'targetNamespace' in e.attrib:
        return e.attrib.get('targetNamespace')
    # FutureWarning: The behavior of this method will change in future
    # versions. Use specific 'len(elem)' or 'elem is not None' test
    # instead.
    if e.getparent() is not None:
        return lookup_schema_target_namespace(e.getparent())

class BaseSchema(BaseElm):
    """
    A basic element type for all elements in the schema namespace.
    """
    NS = 'http://www.w3.org/2001/XMLSchema'

    @property
    def target_namespace(self):
        return lookup_schema_target_namespace(self)

class TagResolver(ET.CustomElementClassLookup):

    def lookup(self, node_type, document, namespace, name):
        if namespace == BaseSchema.NS:
            return BaseSchema
        return BaseElm

parser_lookup = TagResolver()
parser = ET.XMLParser()
parser.set_element_class_lookup(parser_lookup)

Element = parser.makeelement
SubElement = ET.SubElement


def fromstring(string):
    return ET.fromstring(string, parser=parser)

def parse(fileio):
    return ET.parse(fileio, parser=parser)

def frompath(path):
    return parse(file(path)).getroot()

