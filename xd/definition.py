# - coding: utf
import sys
import sets

import logging
log = logging.getLogger(__name__)

# Compositors
ALL = 'all'
CHOICE = 'choice'
SEQUENCE = 'sequence'

GROUP = 'group'

# Derivations
RESTRICTION = 'restriction'
EXTENSION = 'extension'

## Secial values ##

# Unbounded is used by particals to signal an un-limited number of
# elements are possible.
UNBOUNDED = sys.maxint
# The actual root of the type hierarchy, ITSELF is the base type of
# anyType.
ITSELF = -1
# GLOBAL SCOPE
GLOBAL = 'global'


def is_complex(other):
    return isinstance(other, ComplexTypeDef)

def ais_simple(other):
    return isinstance(other, SimpleTypeDef)

def is_model_group(other):
    return isinstance(other, ModelGroup)

def is_model_group_def(other):
    return isinstance(other, ModelGroupDef)

def is_elm(other):
    return isinstance(other, ElementDec)

def is_elm_ref(other):
    return isinstance(other, Reference) and other.cls == ElementDec

class DataDict(dict):
    """
    A custom dict that can:

    * Use object notation (syntactic sugar).
    * Use addtion operator to merge others.
    * Use subtraction operator to return differences.
    """

    def __add__(self, other):
        """
        Return copy of this dictionary updated with given dictionary.
        """
        return merge(self, other)

    def __sub__(self, other):
        """
        Return difference of this dictionary with given dictionary.
        """
        return dict_diff(self, other)

    def __getattr__(self, s):
        if s in self:
            return self[s]
        return dict.__getattribute__(self, s)

    def __setattr__(self, s, val):
        method = getattr(dict, s, None)
        if method and isinstance(method, type(dict.keys)):
            raise ValueError("Name clash: " + s)
        self[s] = val

class Reference(object):

    def __init__(self, name, ns, cls):
        self.name = name
        self.ns = ns
        self.cls = cls

    def lookup(self, schema):
        if self.cls == AttributeGroupDef:
            return schema.get_attrgroup(self.ns, self.name)
        if self.cls == ModelGroupDef:
            return schema.get_modelgroup(self.ns, self.name)
        if self.cls == ElementDec:
            return schema.get_element(self.ns, self.name)

class AttributeGroupDef(object):
    """
    Attribute group definition
    """
    def __init__(
            self, name, targetns=None, attributes=None, wildcard=None,
            annotation=None,
        ):
        self.data = DataDict()
        self.name = name
        self.targetns = targetns
        self.attributes = attributes or []
        self.wildcard = wildcard
        self.annotation = annotation

    @property
    def name(self):
        """
        Optional. An NCName
        """
        return self.data.name

    @name.setter
    def name(self, name):
        self.data.name = name

    @property
    def targetns(self):
        """
        Either ·absent· or a namespace name, as defined in
        [XML-Namespaces].
        """
        return self.data.target_namespace

    @targetns.setter
    def targetns(self, targetns):
        """
        A set of attribute uses.
        """
        self.data.target_namespace = targetns

    @property
    def attributes(self):
        """
        Optional. An annotation.
        """
        return self.data.attribute_uses

    @attributes.setter
    def attributes(self, attributes):
        self.data.attribute_uses = attributes

    @property
    def annotation(self):
        return self.data.annotation

    @annotation.setter
    def annotation(self, annotation):
        self.data.annotation = annotation

class AttributeDec(object):
    """
    Attribute Declaration
    """

    def __init__(
            self, name, target_namespace=None, typedef=None, scope=None,
            value_constraint=None, annotation=None,
        ):
        self.data = DataDict()
        self._typename = None
        self._typens = None

        self.name = name
        self.target_namespace = target_namespace
        self.typedef = typedef
        self.scope = scope
        self.value_constraint = value_constraint
        self.annotation = annotation

    @property
    def typename(self):
        """
        While parsing schema documents we may not know the type
        defenition when we encounter the attribute declaration. In those
        cases we'll store the type name and type namespace in typename
        and typens properties respectively. The Schema object is
        responsible for adding the type definition to when it's found.
        """
        return self._typename

    @typename.setter
    def typename(self, name):
        self._typename = name

    @property
    def typens(self):
        """
        Type ns
        """
        return self._typens

    @typens.setter
    def typens(self, name):
        self._typens = name

    @property
    def name(self):
        """
        Optional. An NCName
        """
        return self.data.name

    @name.setter
    def name(self, name):
       self.data.name = name

    @property
    def target_namespace(self):
        """
        Either ·absent· or a namespace name, as defined in [XML-Namespaces].
        """
        return self.data.taget_namespace

    @target_namespace.setter
    def target_namespace(self, target_namespace):
        self.data.target_namespace = target_namespace

    @property
    def typedef(self):
        """
        A simple type definition.
        """
        return self.data.type_definition

    @typedef.setter
    def typedef(self, typedef):
        self.data.type_definition = typedef

    @property
    def scope(self):
        """
        Optional. Either global or a complex type definition.
        """
        return self.data.scope

    @scope.setter
    def scope(self, scope):
        self.data.scope = scope

    @property
    def value_constraint(self):
        """
        Optional. A pair consisting of a value and one of default, fixed.
        """
        return self.data.value_constraint

    @value_constraint.setter
    def value_constraint(self, value_constraint):
        self.data.value_constraint = value_constraint

    @property
    def annotation(self):
        """
        Optional. An annotation.
        """
        return self.data.annotation

    @annotation.setter
    def annotation(self, annotation):
        self.data.annotation = annotation

class AttributeUse(object):
    """
    An attribute use is a utility component which controls the occurrence and
    defaulting behavior of attribute declarations. It plays the same role for
    attribute declarations in complex types that particles play for element
    declarations.
    """
    FIXED = 'fixed'
    DEFAULT = 'default'

    def __init__(self, required=False, attribute=None, value_constraint=None):
        self.data = DataDict()
        self.required = required
        self.attribute = attribute
        self.value_constraint = value_constraint

    @property
    def required(self):
        """
        A boolean, determines whether this use of an attribute
        declaration requires an appropriate attribute information item
        to be present, or merely allows it.
        """
        return self.data.required

    @required.setter
    def required(self, required):
        self.data.required = required

    @property
    def attribute(self):
        """
        provides the attribute declaration itself, which will in turn determine
        the simple type definition used
        """
        return self.data.attribute_declaration

    @attribute.setter
    def attribute(self, attribute):
        self.data.attribute_declaration = attribute

    @property
    def value_constraint(self):
        """
        Optional. A pair consisting of a value and one of default, fixed.
        Allows for local specification of a default or fixed value. This must
        be consistent with that of the attribute declaration
        """
        return self.data.value_constraint

    @value_constraint.setter
    def value_constraint(self, value_constraint):
        self.data.value_constraint = value_constraint

    @property
    def default(self):
        if not self.value_constraint:
            return
        if self.value_constraint[0] == self.DEFAULT:
            return self.value_constraint[1]

    @default.setter
    def default(self, value):
        self.value_constraint = (self.DEFAULT, value)

    @property
    def fixed(self):
        if not self.value_constraint:
            return
        if self.value_constraint[0] == self.FIXED:
            return self.value_constraint[1]

    @fixed.setter
    def fixed(self, value):
        self.value_constraint = (self.FIXED, value)

class Term(object):
    "One of a model group, a wildcard, or an element declaration."

    def __init__(self, data):
        self.data = data

class ModelGroup(object):

    def __init__(self, compositor, particals=None, annotation=None):
        self.compositor = compositor
        self.particals = particals or [] # A list of particles
        self.annotation = annotation #  Optional annotation

    @property
    def compositor(self):
        #One of all, choice or sequence.
        return self._compositor

    @compositor.setter
    def compositor(self, compositor):
        assert compositor in (SEQUENCE, CHOICE, ALL,), \
            'compositor must be in sequence, choice, all'
        self._compositor = compositor


class ModelGroupDef(object):
    ##<group>
    def __init__(self, name, targetns=None, model=None, annotation=None):
        self.data = DataDict()
        self.name = name
        self.targetns = targetns
        self.model = model
        self.annotation = annotation

    @property
    def name(self):
        """
        An NCName as defined by [XML-Namespaces].
        """
        return self.data.name

    @name.setter
    def name(self, name):
        self.data.name = name

    @property
    def targetns(self):
        """
        Either ·absent· or a namespace name, as defined in [XML-Namespaces].
        """
        return self.data.target_namespace

    @targetns.setter
    def targetns(self, targetns):
        self.data.target_namespace = targetns

    @property
    def model(self):
        """
        A ModelGroup
        """
        return self.data.model_group

    @model.setter
    def model(self, model):
        self.data.model_group = model

    @property
    def annotation(self):
        """
        Optional. An annotation.
        """
        return self.data.annotation

    @annotation.setter
    def annotation(self, annotation):
        self.data.annotation = annotation


class ElementDec(object):
    """
    Element Declaration
    """
    def __init__(
        self, name, targetns=None, typedef=None, scope=GLOBAL,
        value_constraint=None, nillable=False, identity_constraints=None,
        substitution_group=None, dissallowed_substitutions=None,
        abstract=False, annotation=None,
        ):
        self.data = DataDict()
        self._typename = None
        self._typens = None
        self.subs = []

        self.name = name
        self.targetns = targetns
        self.typedef = typedef
        self.scope = scope
        self.substitution_group = value_constraint
        self.nillable = nillable
        self.identity_constraints = identity_constraints or []
        self.substitution_group = None
        self.dissallowed_substitutions = None
        self.abstract = False
        self.annotation = None

    @property
    def name(self):
        """
        Optional. An NCName
        """
        return self.data.name

    @name.setter
    def name(self, name):
        """
        Optional. An NCName
        """
        self.data.name = name

    @property
    def typename(self):
        """
        While parsing schema documents we may not know the type defenition when
        we encounter the element declaration. In those cases we'll store the
        type name and type namespace in typename and typens properties
        respectively. The Schema object is responsible for adding the type
        definition to when it's found.
        """
        return self._typename

    @typename.setter
    def typename(self, name):
        self._typename = name

    @property
    def typens(self):
        """
        Type ns
        """
        return self._typens

    @typens.setter
    def typens(self, name):
        self._typens = name

    @property
    def targetns(self):
        """
        The target namespace for this definition, can be None
        """
        return self.data.target_namespace

    @targetns.setter
    def targetns(self, targetns):
        """
        """
        self.data.target_namespace = targetns

    @property
    def typedef(self):
        """
        if none, anyType will be used
        """
        return self.data.type_definition

    @typedef.setter
    def typedef(self, typedef):
        if typedef:
            self.typename = typedef.name
            self.typens = typedef.targetns
        self.data.type_definition = typedef


    @property
    def scope(self):
        """
        Optional. Either global or a complex type definition.

        A {scope} of global identifies element declarations available
        for use in content models throughout the schema. Locally scoped
        declarations are available for use only within the complex type
        identified by the {scope} property. This property is ·absent· in
        the case of declarations within named model groups: their scope
        is determined when they are used in the construction of complex
        type definitions.
        """
        return data.name

    @name.setter
    def scope(self, scope):
        self.data.scope = scope

    @property
    def substitution_group(self):
        """
        Optional. An NCName
        """
        return self.data.substitution_group

    @substitution_group.setter
    def substitution_group(self, substitution_group):
        """
        Optional. An NCName
        """
        self.data.substitution_group = substitution_group

    @property
    def nillable(self):
        """
        Optional. An NCName
        """
        return self.data.nillable

    @nillable.setter
    def nillable(self, nillable):
        """
        Optional. An NCName
        """
        self.data.nillable = nillable

    @property
    def identity_contranits(self):
        """
        Optional. An NCName
        """
        return self.data.identity_contranits

    @identity_contranits.setter
    def identity_contranits(self, identity_contranits):
        """
        Optional. An NCName
        """
        self.data.identity_contranits = identity_contranits

    @property
    def substitution_group(self):
        """
        Optional. An NCName
        """
        return self.data.substitution_group

    @substitution_group.setter
    def substitution_group(self, substitution_group):
        """
        Optional. An NCName
        """
        self.data.substitution_group = substitution_group

    @property
    def dissallowed_substitutions(self):
        """
        Optional. An NCName
        """
        return self.data.dissallowed_substitutions

    @dissallowed_substitutions.setter
    def dissallowed_substitutions(self, dissallowed_substitutions):
        """
        Optional. An NCName
        """
        self.data.dissallowed_substitutions = dissallowed_substitutions

    @property
    def abstract(self):
        """
        Optional. An NCName
        """
        return self.data.abstract

    @abstract.setter
    def abstract(self, abstract):
        """
        Optional. An NCName
        """
        self.data.abstract = abstract

    @property
    def annotation(self):
        """
        Optional. An NCName
        """
        return self.data.annotation

    @annotation.setter
    def annotation(self, annotation):
        """
        Optional. An NCName
        """
        self.data.annotation = annotation


class Partical(object):

    def __init__(self, term, min_occurs=1, max_occurs=1):
        self.data = DataDict()
        self.term = term
        self.min_occurs = int(min_occurs)
        if max_occurs == 'unbounded':
            max_occurs = UNBOUNDED
        self.max_occurs = int(max_occurs)

    @property
    def term(self):
        """
        One of a model group, a wildcard, or an element declaration.
        """
        return self.data.term

    @term.setter
    def term(self, term):
        self.data.term = term

    @property
    def min_occurs(self):
        return self.data.min_occurs

    @min_occurs.setter
    def min_occurs(self, min_occurs):
        self.data.min_occurs = min_occurs

    @property
    def max_occurs(self):
        return self.data.max_occurs

    @max_occurs.setter
    def max_occurs(self, max_occurs):
        self.data.max_occurs = max_occurs

    def emtiable(self):
        self.min_occurs == 0
        # OR
        # Its {term} is a group and the minimum part of the effective total range
        # of that group, as defined by Effective Total Range (all and sequence)
        # (§3.8.6.5) (if the group is all or sequence) or Effective Total Range
        # (choice) (§3.8.6.6) (if it is choice), is 0.

class WildCard(object): pass

EMPTY = 'empty'
SIMPLE = 'simple'
MIXED = 'mixed'
ELONLY = 'element-only'

class ContentType(object):
    EMPTY = 'empty'
    SIMPLE = 'simple'
    MIXED = 'mixed'
    ELONLY = 'element-only'

    def __init__(
        self, variety, partical=None, open_content=None,
        simple_type=None,
        ):
        self.data = DataDict()
        self.variety = variety
        self.partical = partical
        self.open_content = open_content
        self.simple_type = simple_type

    @property
    def variety(self):
        return self.data.variety

    @variety.setter
    def variety(self, variety):
        assert variety in (EMPTY, SIMPLE, MIXED, ELONLY,)
        self.data.variety = variety

    @property
    def partical(self):
        return self.data.partical

    @partical.setter
    def partical(self, partical):
        self.data.partical = partical

    @property
    def open_content(self):
        return self.data.open_content

    @open_content.setter
    def open_content(self, open_content):
        self.data.open_content = open_content

    @property
    def simple_type(self):
        return self.data.simple_type

    @simple_type.setter
    def simple_type(self, simple_type):
        self.data.simple_type = simple_type

    def is_element_only(self):
        return self.variety == ELONLY

    def is_mixed(self):
        return self.variety == MIXED

    #def is_simple(self):
    #j    return isinstance(self.content_type, SimpleTypeDef)

    def is_empty(self):
        return self.content_type == None


class ComplexTypeDef(object):
    """
    Complex type definition
    """
    # Derivation methods
    RESTRICTION = 'restriction'
    EXTENSION = 'extension'

    def __init__(
        self, name=None, targetns=None, basedef=None,
        derivation=RESTRICTION, abstract=False, final=None,
        context=None, attributes=None, wildcard=None, content_type=None,
        prohibited_subs=None, assertions=None, annotations=None,
        ):
        self.data = DataDict()
        self.name = name
        self.targetns = targetns
        self.basedef = basedef
        self.final = final
        self.context = context
        self.derivation = derivation
        self.abstract = abstract
        self.attributes = attributes or []
        self.content_type = content_type
        self.prohibited_subs = prohibited_subs or []
        self.assertions = assertions
        self.annotations = annotations or []


    @property
    def name(self):
        """
        Optional. An NCName
        """
        return self.data.name

    @name.setter
    def name(self, name):
        """
        Optional. An NCName
        """
        self.data.name = name

    @property
    def targetns(self):
        """
        Either ·absent· or a namespace name, as defined in [XML-Namespaces].
        When abset the target namespace is inherited from parent elment.
        """
        return self.data.target_namespace

    @targetns.setter
    def targetns(self, targetns):
        self.data.target_namespace = targetns

    @property
    def basedef(self):
        """
        Either a simple type definition or a complex type definition.
        """
        if self.data.base_type_def == ITSELF:
            return
        return self.data.base_type_def

    @basedef.setter
    def basedef(self, basedef):
        self.data.base_type_def = basedef

    @property
    def derivation(self):
        """
        Either extension or restriction.
        """
        return self.data.derivation_method

    @derivation.setter
    def derivation(self, derivation):
        assert derivation in (EXTENSION, RESTRICTION,)
        self.data.derivation_method = derivation

    @property
    def final(self):
        """
        A subset of {extension, restriction}.

        A complex type with an empty specification for {final} can be
        used as a {base type definition} for other types derived by
        either of extension or restriction; the explicit values
        extension, and restriction prevent further derivations by
        extension and restriction respectively. If all values are
        specified, then [Definition:]  the complex type is said to be
        final, because no further derivations are possible. Finality is
        not inherited, that is, a type definition derived by restriction
        from a type definition which is final for extension is not
        itself, in the absence of any explicit final attribute of its
        own, final for anything.
        """
        return self.data.final

    @final.setter
    def final(self, v):
        if v == '#All':
            self.data.final = (EXTENSION, RESTRICTION,)
        elif v == 'extension':
            self.data.final = (EXTENSION,)
        elif v == 'restriction':
            self.data.final = (RESTRICTION,)
        elif not v:
            self.data.final = ()
        else:
            raise ValueError, v

    @property
    def context(self):
        """
        Required for anonymous types.
        The context property is only relevant for anonymous type
        definitions, for which its value is the component in which this
        type definition appears as the value of a property, e.g.  Either
        an Element Declaration or a Complex Type Definition.
        """
        return self.data.context

    @context.setter
    def context(self, context):
        self.data.context = context

    @property
    def abstract(self):
        """
        A boolean, when set the type definition can not be 'used for
        validation', that is, they can not be the type of an attribute
        or element. Only a base type of another type.
        """
        return self.data.abstract

    @abstract.setter
    def abstract(self, abstract):
        """
        Optional. An NCName
        """
        self.data.abstract = abstract

    @property
    def attributes(self):
        """
        A set of attribute uses.
        """
        return self.data.attribute_uses

    @attributes.setter
    def attributes(self, attribute_uses):
        """
        Optional. An NCName
        """
        self.data.attribute_uses = attribute_uses

    @property
    def wildcard(self):
        """
        Optional. A wildcard.
        {attribute wildcard}s provide a more flexible specification for
        ·validation· of attributes not explicitly included in {attribute
        uses}. Informally, the specific values of {attribute wildcard}
        are interpreted as follows:

        * any: [attributes] can include attributes with any qualified or
          unqualified name.
        * a set whose members are either namespace names or ·absent·:
          [attributes] can include any attribute(s) from the specified
          namespace(s). If ·absent· is included in the set, then any
          unqualified attributes are (also) allowed.
        * 'not' and a namespace name: [attributes] cannot include
          attributes from the specified namespace.
        * 'not' and ·absent·: [attributes] cannot include unqualified
          attributes.
        """
        return self.data.wildcard

    @wildcard.setter
    def wildcard(self, wildcard):
        """
        Optional. An NCName
        """
        self.data.wildcard = wildcard

    @property
    def content_type(self):
        """
        """
        return self.data.content_type

    @content_type.setter
    def content_type(self, content_type):
        """
        Optional. An NCName
        """
        self.data.content_type = content_type

    @property
    def prohibited_subs(self):
        """
        prohibited substitutions
        """
        return self.data.prohibited_substitutions

    @prohibited_subs.setter
    def prohibited_subs(self, v):
        """
        Optional. An NCName
        """
        if v == '#All':
            self.data.prohibited_substitutions = (EXTENSION, RESTRICTION,)
        elif v == 'extension':
            self.data.prohibited_substitutions = (EXTENSION,)
        elif v == 'restriction':
            self.data.prohibited_substitutions = (RESTRICTION,)
        elif not v:
            self.data.prohibited_substitutions = ()
        else:
            raise ValueError

    @property
    def annotations(self):
        """
        A set ofannotations
        """
        return self.data.annotation

    @annotations.setter
    def annotations(self, annotations):
        """
        A set of annotations
        """
        self.data.annotation = annotations

ATOMIC = 'atomic'
LIST = 'list'
UNION = 'union'

class SimpleTypeDef(object):
    """
    Simple type definition
    """

    def __init__(
        self, name, targetns=None, variety=None, facets=None,
        fundimentals=None, basedef=None, final=None,
        annotation=None, primative=None,
        ):
        self.data = DataDict()
        self._primative = None
        self._valid_facets = {}

        self.name = name
        self.targetns = targetns
        self.variety = variety
        self.facets = facets or {}
        self.fundimentals = fundimentals or []
        self.basedef = basedef
        self.final = final
        self.annotation = annotation
        self.primative = primative

    @property
    def name(self):
        """
        Optional. An NCName
        """
        return self.data.name

    @name.setter
    def name(self, name):
        self.data.name = name

    @property
    def targetns(self):
        """
        Either absent or a namespace name
        """
        return self.data.target_namespace

    @targetns.setter
    def targetns(self, targetns):
        self.data.target_namespace = targetns

    @property
    def variety(self):
        """
        One of {atomic, list, union}
        """
        return self.data.variety

    @variety.setter
    def variety(self, variety):
        assert variety in (None, ATOMIC, LIST, UNION), variety
        self.data.variety = variety

    @property
    def facets(self):
        """
        A possibly empty set of Facets
        """
        return self.data.facets

    @facets.setter
    def facets(self, facets):
        self.data.facets = facets

    @property
    def fundimentals(self):
        """
        A set of Fundamental facets
        """
        return self.data.fundimental_facets

    @fundimentals.setter
    def fundimentals(self, fundimentals):
        self.data.fundimental_facets = fundimentals

    @property
    def basedef(self):
        """
        If the datatype has been ·derived· by ·restriction· then the Simple
        Type Definition component from which it is ·derived·, otherwise the
        Simple Type Definition for anySimpleType
        """
        return self.data.base_type_definition

    @basedef.setter
    def basedef(self, basedef):
        self.data.base_type_definition = basedef

    @property
    def final(self):
        """
        A subset of {restriction, list, union}.
        """
        return self.data.final

    @final.setter
    def final(self, final):
        self.data.final = final

    @property
    def annotation(self):
        """
        Optional. An annotation.
        """
        return self.data.annotation

    @annotation.setter
    def annotation(self, annotation):
        self.data.annotation = annotation

    @property
    def primative(self):
        if self._primative:
            return self._primative
        return self.basedef.primative

    @primative.setter
    def primative(self, method):
        self._primative = method

    @property
    def valid_facets(self):
        """
        Readonly. Valid facets for this type. Instances of these classes can be
        added to the SimpleTypeDef.facets property.
        """
        if not self._valid_facets:
            return self.basedef.valid_facets
        return self._valid_facets

    def add_facet(self, name, restriction):
        assert name in self.valid_facets, name
        from builtins import FACETS
        if name in self.facets:
            facet = self.facets[name]
            facet.restriction.append(restriction)
        else:
            facet = FACETS[name](restriction)
        self.facets[facet.name] = facet

