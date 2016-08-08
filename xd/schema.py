import os
from xd.definition import (
     SEQUENCE, ALL, CHOICE, GROUP, RESTRICTION, EXTENSION, ElementDec, ComplexTypeDef,
     ContentType, SimpleTypeDef, ModelGroup, Partical, is_complex, ais_simple,
     is_elm, AttributeDec, AttributeUse, ModelGroupDef, AttributeGroupDef,
     Reference, is_elm_ref, WildCard, ELONLY, MIXED, ITSELF,
)
from xd.builtins import BUILTINS, XSI, XS, anySimpleType, anyType
from xd.etree import QName, frompath

# A map of property/attribute names that would clash with python builtins or
# otherwise should be overriden.
renames = {
  'class': 'classenum',
  'object': 'object_type',
  'from': 'frm',
}


def attr_namer(name, renames=renames):
    """
    Change names comming from xml so they don't clash with python
    builtin names.
    """
    if name in renames:
        return renames[name]
    return name

class SchemaConstructionError(Exception):
    """
    Raised when there is an error constructing a valid schema
    definition.
    """

class SchemaValidityError(Exception):
    """
    Raised when a schema instance does not conform to it's schema
    definition.
    """

# Descriptors for type implimentations

class ParticalGetter(object):
    """
    A descriptor used to retrieve a partical from a schema instance.
    """

    def __init__(self, partical, sub=None):
        self.partical = partical

    def __get__(self, obj, objtyp):
        partical = self.partical
        if partical.min_occurs <= 1 and partical.max_occurs <= 1:
            for cld in obj.et.iterchildren():
                if cld.tagname == partical.term.name:
                    return obj.schema.instance(cld, partical.term)
        else:
            return self.iterchildren(obj, partical)

    def iterchildren(self, obj, partical):
        for cld in obj.et.iterchildren():
            if cld.tagname == partical.term.name:
                yield obj.schema.instance(cld, partical.term)
            for sub in partical.term.subs:
                if cld.tagname == sub.name:
                    yield obj.schema.instance(cld, sub)

class AttributeGetter(object):
    """
    A descriptor used to retrieve an attribute froma schema instance
    based on it's definition's AttributeUse.
    """

    def __init__(self, attruse):
        self.attruse = attruse

    def __get__(self, obj, objtyp):
        attruse = self.attruse
        name = attruse.attribute.name
        if not attruse.attribute.typedef:
            attruse.attribute.typedef = obj.schema.get_type(
                attruse.attribute.typens, attruse.attribute.typename
            )
        assert attruse.attribute.typedef, \
            (attruse.attribute.typens, attruse.attribute.typename)
        cls = simple_type_factory(
            attruse.attribute.name,
            attruse.attribute.typedef,
        )
        # TODO: This checks Local schema validity while returning the
        # value.  mixing schema validity checks and schema object
        # implimentation may not be desired.
        # http://www.w3.org/TR/xmlschema-1/#cvc-attribute
        if name not in obj.et.attrib and attruse.required:
            raise SchemaValidityError("Missing required attribute", name)
        if name not in obj.et.attrib and attruse.fixed:
            val = attruse.fixed
        elif name not in obj.et.attrib and attruse.default:
            val = attruse.default
        else:
            val = obj.et.attrib.get(name)
        return cls(val)()

# Type implimentation classes

def simple_type_factory(name, definition):
    cls = type(name, (SimpleTypeImp,), dict())
    cls.definition = definition
    return cls

class SimpleTypeImp(object):
    """
    Impliment the xml schema simple type system. Simple types provide access
    the the data of xml schema instance element attributes or the charachter
    contents of an element. When implimented this class is used by the return
    the data cast and validated according to the simple type definition.
    """
    definition = None

    def __init__(self, value):
        self.value = value

    def __call__(self):
        if self.value:
            self.validate(self.value)
            return self.cast(self.value)

    @classmethod
    def cast(cls, value):
        return cls.definition.primative(value)

    @classmethod
    def validate(cls, value):
        for s in cls.definition.facets:
            facet = cls.definition.facets[s]
            assert facet(value), (facet.restriction, value)

def complex_model(model, d, schema):
    for partical in model.particals:
        if isinstance(partical.term, Reference):
            partical.term = partical.term.lookup(schema)
        if isinstance(partical.term, ModelGroupDef):
            complex_model(partical.term.model, d, schema)
        elif isinstance(partical.term, ModelGroup):
            complex_model(partical.term, d, schema)
        elif isinstance(partical.term, ElementDec):
            #if partical.term.subs:
            #    for sub in partical.term.subs:
            #        d[attr_namer(sub.name)] = ParticalGetter(partical, sub=sub)
            d[attr_namer(partical.term.name)] = ParticalGetter(partical)
        elif isinstance(partical.term, WildCard):
            pass

def complex_attributes(attributes, d, schema):
    for attruse in attributes:
        if isinstance(attruse, Reference):
            attruse = attruse.lookup(schema)
        if isinstance(attruse, AttributeGroupDef):
            complex_attributes(attruse.attributes, d, schema)
        #elif isinstance(attruse, AttributeDec):
        else:
            d[attr_namer(attruse.attribute.name)] = AttributeGetter(attruse)

def complex_type_factory(name, definition, schema):
    """
    Create a new subclass of ComplexImp with the given name and class
    level definition. When the classes type definition has a base type
    associated with it, a class for the base type will be created and
    the class returned by this method will be a subclass of that base
    type class.
    """
    d = dict()
    basecls = None
    basedef = definition.basedef
    if basedef and basedef != ITSELF:
        basecls = complex_type_factory(basedef.name, basedef, schema)
    if definition.content_type.is_element_only():
        model = definition.content_type.partical.term
        complex_model(model, d, schema)
    complex_attributes(definition.attributes, d, schema)
    cls = type(name, (basecls or ComplexImp,), d)
    cls.definition = definition
    return cls

class ComplexImp(object):
    """
    Base class for all complex type implimentations. This class holds; a
    class level type definition (definition), A schema instance
    etree.Element (et), and a schema object (schema). The defenition is
    used by a type facotory method to add Partical and Attribute
    Descriptors which provide access to the elements data.
    """
    definition = None # Defined by subclass

    def __init__(self, et, schema):
        self.et = et
        self.schema = schema

    def __iter__(self):
        for cld in self.et.iterchildren():
            yield self.schema.instance(cld)


def handle_schema(schema, et):
    #target_namespace = et.attrib.get('targetNamespace', None)
    for cld in et.iterchildren():
        if cld.tagname == 'element':
            dec = schema.parse(cld)
        elif cld.tagname == 'complexType':
            typedef = schema.parse(cld)
        elif cld.tagname == 'simpleType':
            typedef = schema.parse(cld)
        elif cld.tagname == 'group':
            group = schema.parse(cld)
        elif cld.tagname == 'attributeGroup':
            group = schema.parse(cld)
        elif cld.tagname == 'import':
            doc = schema.parse(cld)
        elif cld.tagname == 'include':
            doc = schema.parse(cld)
        else:
#            warn("Unhandled schema child", cld.tagname)
            pass

def define_complex(schema, et):
    # Common mapping rules for complex type definitions
    typ = ComplexTypeDef(
        name = et.attrib.get('name'),
        targetns = et.target_namespace,
    )
    if 'block' in et.attrib:
        typ.prohibited_subs = e.attrib['block']
    if 'final' in et.attrib:
        typ.prohibited_subs = e.attrib['final']
    if not typ.name:
        # The parent element of a complex type definition
#        Warn('Not handling anonymous type')
        pass
    # TODO: Assertions

    # Not child elements
    if not len(et):
        return
    # Mapping Rules for Complex Types with Simple Content
    if et[0].tagname == 'simpleContent':
        content = et[0]
        assert len(content) == 1
        derivation = content[0]
        typ.derivation == derivation.tagname
        qname = QName(et, derivation.attrib.get('base'))
        typ.basedef = schema.get_type(
            qname.namespace,
            qname.localname,
        )
        typ.content_type = ContentType(
            variety=ContentType.SIMPLE,
            partical=None,
            open_content=None,
        )
        if (
            is_complex(typ.basedef) and
            typ.basedef.content_type.variety == ContentType.SIMPLE and
            typ.derivation == ComplexTypeDef.RESTRICTION
            ):
            if et[0].tagname == 'restriction':
                if len(et[0]) and et[0][0].tagname == 'simpleType':
                    simpdef = handle_simple(et[0][0])
                else:
                    pass
        elif (
            is_complex(typ.basedef) and
            typ.basedef.content_type.variety == ContentType.MIXED and
            typ.content_type.partical.isemtiable()
            ):
            pass #2
        elif (
            is_complex(typ.basedef) and
            typ.basedef.content_type.variety == ContentType.SIMPLE and
            typ.derivation == ComplexTypeDef.EXTENSION
            ):
            pass # 3
        elif (
            ais_simple(typ.basedef) and
            typ.derivation == ComplexTypeDef.EXTENSION
            ):
            pass # 4
        else:
            typ.content_type.simple_type = anySimpleType
        parent = derivation
    # Mapping Rules for Complex Types with Complex Content
    else:
        # Any complex type definition which does not have a
        # simpleContent child element is considered to have complex
        # content. The complex content can come in two forms, explicit
        # (when there is a Complex Content child) and implicit (when the
        # child is group, choice sequnce).

        content = et[0]
        # Mapping rules for Complxt Type Definition with Explicit
        # Complex Content
        if content.tagname == 'complexContent':
            derivation = content[0]
            typ.derivation == derivation.tagname
            qname = QName(et, derivation.attrib.get('base'))
            typ.basedef = schema.get_type(
                qname.namespace,
                qname.localname,
            )
            #assert typ.basedef
            mixed = content.attrib.get('mixed', False)
            parent = derivation
        # Mapping Rules for Complex Types with Implicit Complex Content
        else:
            typ.derivation = ComplexTypeDef.RESTRICTION
            typ.basedef = anyType
            mixed = et.attrib.get('mixed', False)
            parent = et
        explicit = None
        effective = None
        # Determine explicit content
        for cld in parent.iterchildren():
            # 2.1.1
            if cld.tagname in (GROUP, SEQUENCE, ALL, CHOICE,):
                # 2.1.2
                if cld.tagname in (ALL, SEQUENCE) and len(cld) == 0:
                    continue
                # 2.1.3
                if (
                    cld.tagname == CHOICE and cld.attrib.get('minOccurs') == 0
                    and not annotate_only
                    ):
                    for b in cld.iterchildren():
                        if b.tagname != 'annotation':
                            annotate_only = True
                    if annotate_only:
                        continue
                # 2.1.4
                if (
                    cld.tagname in (GROUP, SEQUENCE, ALL, CHOICE) and
                    cld.attrib.get('maxOccurs') == 0
                    ):
                        continue
                explicit = Partical(
                    term = handle_mg(schema, cld),
                    min_occurs = cld.attrib.get('minOccurs', 1),
                    max_occurs = cld.attrib.get('maxOccurs', 1)
                )
        # 3.1
        if not explicit:
            # 3.1.1
            if mixed:
                effective = Partical(
                    term=ModelGroup(SEQUENCE),
                    min_occurs = 1,
                    max_occurs = 1,
                )
            # 3.1.2
        else:
            # 3.2
            effective = explicit
        # determin explicit content type
        # 4.1
        if typ.derivation == RESTRICTION:
            if not effective:
                typ.content_type = ContentType(
                   MIXED if mixed else ELONLY
                )
            else:
                typ.content_type = ContentType(
                    variety=MIXED if mixed else ELONLY,
                    partical=effective,
                )
        else: # EXTENSION
            # 4.2.1
            if (
                ais_simple(typ.basedef) or
                    (
                        is_complex(typ.basedef)  and (
                            typ.content_type.variety in (SIMPLE, EMPTY,),
                        )
                    )
                ):
                if not effective:
                    typ.content_type = ContentType()
                else:
                    typ.content_type = ContentType(
                        variety=MIXED if mixed else ELONLY,
                        partical=effective,
                    )
            # 4.2.2
            if (
                is_complext(typ.basedef) and
                typ.content_type in (ELONLY, MIXED,) and
                not effective
                ):
                typ.contant_type = typ.basedef.content_type
            # 4.2.3
            else:
                pass
                #typ.content_type = ContentType(
                #    variety=MIXED if mixed else ELONLY,
                #    partical=Partical(
                #        
                #    )
                #)
    # Map attribute uses
    for cld in parent.iterchildren():
        if cld.tagname == 'attribute':
            typ.attributes.append(schema.parse(cld))
        elif cld.tagname == 'attributeGroup':
            typ.attributes.append(schema.parse(cld))
    if typ.name:
        schema.add_type(typ)
    return typ

def complex_children(schema, et, typ):
    """
    Handle the children of a complexType or extension. This is called by
    handle_complex but can also be used recursivly when the
    ComplexTypeDef has a derivation method of extension (tag
    complexContent with a child tag extension).
    """
    MIXED = ContentType.MIXED
    SIMPLE = ContentType.SIMPLE
    ELONLY = ContentType.ELONLY
    EXTENSION = ComplexTypeDef.EXTENSION
    RESTRICTION = ComplexTypeDef.RESTRICTION
    for cld in et.iterchildren():
        if cld.tagname == 'complexContent':
            if len(cld) != 1:
                raise SchemeConstructionError(
                    'Wrong number of children: {0}'.format(len(cld))
                )
            derivation = cld[0]
            typ.derivation = derivation.tagname
            assert 'base' in derivation.attrib
            qname = QName(derivation, derivation.attrib['base'])
            typ.basedef = schema.get_type(
                qname.namespace,
                qname.localname,
            )
            assert typ.basedef, derivation.attrib['base']
            complex_children(schema, derivation, typ)
        elif cld.tagname == 'simpleContent':
            if len(cld) != 1:
                raise SchemeConstructionError(
                    'Wrong number of children: {0}'.format(len(cld))
                )
            derivation = cld[0]
            typ.derivation = derivation.tagname
            assert 'base' in derivation.attrib
            qname = QName(derivation, derivation.attrib['base'])
            typ.basedef = schema.get_type(
                qname.namespace,
                qname.localname,
            )
            assert typ.basedef, derivation.attrib['base']
            if typ.derivation == typ.EXTENSION:
                if ais_simple(typ):
                    typ.content_type = (typ, SIMPLE,)
            #simple_children(schema, derivation, typ)
        elif cld.tagname in (SEQUENCE, ALL, CHOICE,):
            # Returns a modelgroup
            model = schema.parse(cld)
            typ.content_type = ContentType(
                variety=MIXED if et.attrib.get('mixed', False) else ELONLY,
                partical=Partical(
                    term=model,
                    min_occurs=1,
                    max_occurs=1,
                ),
            )
        if cld.tagname in ('attribute', 'attributeGroup',):
            typ.attributes.append(schema.parse(cld))

def handle_complex(schema, et):
    typ = ComplexTypeDef(
        name = et.attrib.get('name'),
        targetns = et.target_namespace,
    )
    complex_children(schema, et, typ)
    if typ.name:
        schema.add_type(typ)
    return typ

def handle_simple(schema, et):
    typedef = SimpleTypeDef(
        name=et.attrib.get('name'),
        targetns=et.target_namespace,
    )
    for a in et.iterchildren():
        if a.tagname == 'restriction':
            qname = QName(a, a.attrib.get('base'))
            typedef.basedef = schema.get_type(qname.namespace, qname.localname)
            assert typedef.basedef, (qname.namespace, qname.localname)
            for b in a.iterchildren():
                if b.tagname == 'comment':
                    continue
                typedef.add_facet(b.tagname, b.attrib.get('value'))
    if typedef.name:
        schema.add_type(typedef)
    return typedef

def handle_mg(schema, et):
    model = ModelGroup(et.tagname)
    for cld in et.iterchildren():
        if cld.tagname == 'element':
            p = Partical(
               term=schema.parse(cld),
               min_occurs = cld.attrib.get('minOccurs', 1),
               max_occurs = cld.attrib.get('maxOccurs', 1),
            )
            model.particals.append(p)
        elif cld.tagname == 'choice':
            p = Partical(
                term=schema.parse(cld),
                min_occurs = cld.attrib.get('minOccurs', 1),
                max_occurs = cld.attrib.get('maxOccurs', 1),
            )
            model.particals.append(p)
        elif cld.tagname == 'group':
            p = Partical(
                term=schema.parse(cld),
                min_occurs = cld.attrib.get('minOccurs', 1),
                max_occurs = cld.attrib.get('maxOccurs', 1),
            )
            model.particals.append(p)
    return model

def handle_element(schema, et):
    if 'ref' in et.attrib:
        qname = QName(et, et.attrib['ref'])
        return Reference(qname.localname, qname.namespace, ElementDec)
    dec = ElementDec(name=et.attrib.get('name'), targetns=et.target_namespace)
    if 'type' in et.attrib:
        qname = QName(et, et.attrib['type'])
        dec.typedef = schema.get_type(qname.namespace, qname.localname)
        if not dec.typedef:
            dec.typename = qname.localname
            dec.typens = qname.namespace
    if 'substitutionGroup' in et.attrib:
        qname = QName(et, et.attrib['substitutionGroup'])
        elm = schema.get_element(qname.namespace, qname.localname)
        assert elm
        dec.substitution_group = elm
        elm.subs.append(dec)
    for cld in et.iterchildren():
        if cld.tagname == 'complexType':
            typ = schema.parse(cld)
            dec.typedef = typ
        if cld.tagname == 'simpleType':
            typ = schema.parse(cld)
            dec.typedef = typ
    schema.add_element(dec)
    #schema.elements[dec.name] = dec
    return dec

def handle_attribute(schema, et):
    attruse = AttributeUse()
    DEFAULT = AttributeUse.DEFAULT
    FIXED = AttributeUse.FIXED
    attruse.attribute = AttributeDec(
        name = et.attrib.get('name'),
    )
    # Populate the attribute use definition by looking at the attribute
    # element's 'use', 'default', or 'fixed' attributes if they exist.
    if 'use' in et.attrib:
        if et.attrib['use'] == 'required':
            attruse.required = True
        else:
            pass
    if DEFAULT in et.attrib:
        attruse.default =  et.attrib[DEFAULT]
    elif FIXED in et.attrib:
        attruse.fixed = et.attrib[FIXED]

    # A type attribute specified a base type definition for this
    # attribute.
    if 'type' in et.attrib:
        # TODO: It might makse sense to just capture the QName info and
        # resolve this later on since its likey it wont resolve at this
        # point.
        qname = QName(et, et.attrib['type'])
        typedef = schema.get_type(qname.namespace, qname.localname)
    else:
        # Anonymous type definition
        for cld in et.iterchildren():
            if cld.tagname == 'simpleType':
                typedef = schema.parse(cld)
            elif cld.tagname == 'annotation':
                pass
            else:
                template = ("attribute elements can only contain simpleType ",
                            "and annotation elements got: {0}")
                msg = template.format(et.tagname)
                raise SchemaValidityError(msg)
    # A typedef or at least a qname is neede so schema.get_type can be
    # tried again later (When constructing the implimentation class).
    assert typedef or qname
    if typedef:
        attruse.attribute.typedef = typedef
    else:
        attruse.attribute.typename = qname.localname
        attruse.attribute.typens = qname.namespace
    return attruse

def handle_model_group(schema, et):
    if 'ref' in et.attrib:
        qname = QName(et, et.attrib['ref'])
        return Reference(qname.localname, qname.namespace, ModelGroupDef)
    group = ModelGroupDef(et.attrib.get('name'), et.target_namespace)
    for cld in et.iterchildren():
        if cld.tagname in (SEQUENCE, ALL, CHOICE,):
            # Returns a modelgroup
            group.model = schema.parse(cld)
    schema.add_modelgroup(group)
    return group

def handle_attr_group(schema, et):
    if 'ref' in et.attrib:
        qname = QName(et, et.attrib['ref'])
        return Reference(qname.localname, qname.namespace, AttributeGroupDef)
    group = AttributeGroupDef(et.attrib['name'], et.target_namespace)
    for cld in et.iterchildren():
        if cld.tagname == 'attribute':
            group.attributes.append(schema.parse(cld))
    schema.add_attrgroup(group)
    return group

def handle_document(schema, et):
    namespace = et.attrib['namespace']
    location = et.attrib['schemaLocation']
    if namespace in schema.docs:
        if location in schema.docs[namespace]:
            return
    doc = schema.resolver(namespace, location)
    if doc is not None:
        schema.parse(doc)
        return
    # This isn't a problem if the schema will be added later but its
    # probably a good idea to add the schemas in order with base imports
    # first when then document resolver won't be able to resolve them.
    #warn(
    #    "Unable to locate document referenced by import or include",
    #    namespace,
    #    location,
    #)

def handle_redifine(sechma, et):
    pass

class DocumentResolver(object):
    """
    Resolve document locations
    """

    def __init__(self, *paths):
        self.dirs = set()
        for a in paths:
            self.notify(a)

    def __call__(self, namespace, location):
        for a in self.dirs:
            path = os.path.join(a, location)
            if os.path.exists(path):
                et = frompath(path)
                if et.target_namespace == namespace:
                    return et

    def notify(self, path):
        if path.endswith('.xsd'):
            path, _ = os.path.split(path)
        self.dirs.add(path)

class Schema(object):
    """
    The Schema object handles the parsing of a schema document(s) as a
    whole.
    """
    default_resolver_class = DocumentResolver

    # Handlers used when parsing schema elements.
    default_handlers = {}
    default_handlers['schema'] = handle_schema
    default_handlers['element'] = handle_element
    default_handlers['complexType'] = define_complex #handle_complex
    default_handlers['simpleType'] = handle_simple
    default_handlers['sequence'] = handle_mg
    default_handlers['choice'] = handle_mg
    default_handlers['attribute'] = handle_attribute
    default_handlers['group'] = handle_model_group
    default_handlers['attributeGroup'] = handle_attr_group
    default_handlers['include'] = handle_document
    default_handlers['import'] = handle_document

    def __init__(self, *paths, **opts):
        #self.target_namepace = opts.get('target_namespace', None)
        self.docs = opts.get('docs', {None: set()})
        # A set of named simple and complex type definitions.
        self.types = opts.get('types', {None: {}})
        # A set of named (top-level) attribute declarations.
        self.attributes = opts.get('attributes', {})
        # A set of named (top-level) element declarations.
        self.elements = opts.get('elements ', {None: {}})
        # A set of named attribute group definitions.
        self.attrgroups = opts.get('attrgroups', {})
        # A set of named model group definitions.
        self.modelgroups = opts.get('modelgroups', {})
        # A set of notation declarations.
        self.notations = opts.get('notations', [])
        # A set of annotations.
        self.annotations = opts.get('annotations', [])
        # Handlers for parsing schema document elements.
        self.handlers = opts.get('handlers', self.default_handlers)

        # Instantiate a document resolver.
        resolver_class = opts.get(
            'resolver_class',
            self.default_resolver_class,
        )
        resolver_opts = opts.get('resolver_opts', {})
        self.resolver = resolver_class(**resolver_opts)

        # Parse and documents given via the paths option
        for a in paths:
            if a.endswith('.xsd'):
                et = etree.frompath(a)
                self.parse(a)
            else:
                self.resolver.notify(a)

    # TODO: self.docs doesn't provide much value. Can probably wean off
    # it and instead just notify the DocumentResolver
    def add_doc(self, et):
        """
        Add a scheme document to the document cache. Schema element
        which are added to the schema without a file on have their
        target namespace accounted for.
        """
        if et.target_namespace not in self.docs:
            self.docs[et.target_namespace] = set()
        if et.target_namespace not in self.types:
            self.types[et.target_namespace] = {}
        if et.target_namespace not in self.elements:
            self.elements[et.target_namespace] = {}
        if et.docfile:
            assert et.docfile not in self.docs[et.target_namespace], \
            (et.docfile, et.target_namespace)
            self.resolver.notify(et.docpath)
        self.docs[et.target_namespace].add(et.docfile)

    def get_doc(self, ns, file):
        if ns in self.docs:
            if file in self.docs[ns]:
                return True

    def add_element(self, element):
        if element.targetns not in self.elements:
            self.elements[element.targetns] = {}
        self.elements[element.targetns][element.name] = element

    def get_element(self, ns, name):
        if ns in self.elements and name in self.elements[ns]:
            return self.elements[ns][name]

    def add_attribute(self, attribute):
        if attribute.targetns not in self.attributes:
            self.attributes[attribute.targetns] = {}
        self.attributes[attribute.targetns][attribute.name] = attribute

    def get_attribute(self, ns, name):
        if ns in self.attributes and name in self.attributes[ns]:
            return self.attributes[ns][name]

    def add_type(self, typedef):
        if typedef.targetns not in self.types:
            self.types[typedef.targetns] = {}
        self.types[typedef.targetns][typedef.name] = typedef
        # Map this type definition to existing element delerations
        for s in self.elements[typedef.targetns]:
            dec = self.elements[typedef.targetns][s]
            if dec.typename == typedef.name:
                dec.typedef = typedef

    def get_type(self, ns, name):
        if ns in (XSI, XS,) and name in BUILTINS:
            return BUILTINS[name]
        if ns in self.types and name in self.types[ns]:
            return self.types[ns][name]

    def add_modelgroup(self, modelgroup):
        if modelgroup.targetns not in self.modelgroups:
            self.modelgroups[modelgroup.targetns] = {}
        self.modelgroups[modelgroup.targetns][modelgroup.name] = modelgroup

    def get_modelgroup(self, ns, name):
        if ns in self.modelgroups and name in self.modelgroups[ns]:
            return self.modelgroups[ns][name]

    def add_attrgroup(self, attrgroup):
        if attrgroup.targetns not in self.attrgroups:
            self.attrgroups[attrgroup.targetns] = {}
        self.attrgroups[attrgroup.targetns][attrgroup.name] = attrgroup

    def get_attrgroup(self, ns, name):
        if ns in self.attrgroups and name in self.attrgroups[ns]:
            return self.attrgroups[ns][name]

    def parse(self, et):
        doc = self.get_doc(et.target_namespace, et.docfile)
        if not doc is not None:
            self.add_doc(et)
        return self.handlers[et.tagname](self, et)

    def instance(self, et, declaration=None):
        # When the scheme instance element has a document root
        # associated with it add that path to the document resolver.
        if et.docroot:
            self.resolver.notify(et.docroot)

        # Check for a schemaLocation attribute and try make sure we can
        # resolve all the locations
        qname = QName(et)
        qname.namespace = XSI
        qname.localname = 'schemaLocation'
        a = qname.qualified()
        if a in et.attrib:
            l = et.attrib[a].split()
            # list of namspace, location pairs
            docs = [(l[n-1], i) for n, i in enumerate(l) if n % 2]
            for ns, loc in docs:
                if self.get_doc(ns, loc):
                    continue
                doc = self.resolver(ns, loc)
                if doc is not None:
                    self.parse(doc)
        if not declaration:
            #assert et.tagname in self.elements
            declaration = self.get_element(et.namespace, et.tagname)
            assert declaration
            #declaration = self.elements[et.tagname]
        typedef = declaration.typedef
        if not typedef:
            typedef = self.get_type(declaration.typens, declaration.typename)
            assert typedef
        if is_complex(typedef):
            qname = QName(et)
            qname.namespace = XSI
            qname.localname = 'type'
            attrname = qname.qualified()
            if attrname in et.attrib:
                qname = QName(et, et.attrib[attrname])
                attrtype = self.get_type(qname.namespace, qname.localname)
                # TODO: This probably needs a method that will recurse up the
                # type hierarchy, for now just using a simple assert to cover
                # the what is in our test cases (hopefully)
                assert attrtype.basedef == typedef
                typedef = attrtype
            cls = complex_type_factory(declaration.name, typedef, self)
            return cls(et, self)
        else:
            assert ais_simple(typedef), (typedef, et.namespace, et.tagname,)
            cls = simple_type_factory(declaration.name, typedef)
            return cls(et.text)()
