from datetime import datetime
import re
from xd.definition import (
    SimpleTypeDef, ComplexTypeDef, RESTRICTION, ITSELF, SEQUENCE, UNBOUNDED,
    Partical, ModelGroup, WildCard, DataDict, ContentType
)


XS = 'http://www.w3.org/2001/XMLSchema'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'

MIXED = ContentType.MIXED

# Facets

class Facet(object):
    name = '' # Defined by sub-class
    def __init__(self, restriction):
        self.restriction = restriction
    def __call__(self, value):
        pass # Defined by sub-class
    def __repr__(self):
        return "<{0}.{1}(restriction={2})>".format(
            __name__, self.__class__.__name__, self.restriction
        )

class length(Facet):
    name = 'length'
    def __init__(self, restriction):
        self.restriction = int(restriction)
    def __call__(self, value):
        return len(value) == self.restriction

class maxlength(Facet):
    name = 'maxLength'
    def __init__(self, restriction):
        self.restriction = int(restriction)
    def __call__(self, value):
        return len(value) <= self.restriction

class minlength(Facet):
    name = 'minLength'
    def __init__(self, restriction):
        self.restriction = int(restriction)
    def __call__(self, value):
        return len(value) >= self.restriction

class pattern(Facet):
    name = 'pattern'
    def __call__(self, value):
        m = re.compile(self.restriction).match(value)
        return m is not None

class enumeration(Facet):
    name = 'enumeration'
    def __init__(self, restriction):
        self.restriction = [restriction]
    def __call__(self, value):
        return value in self.restriction

class whitespace(Facet):
    """
    The whitespace facet constrains the value of types derived from string

    whitespace.restriction must be one of: preserve, replace, collapse

    preserve
        No normalization is done, the value is not changed
    replace
        All occurrences of #x9 (tab), #xA (line feed) and #xD (carriage
        return) are replaced with #x20 (space)
    collapse
        After the processing implied by replace, contiguous sequences of
        #x20's are collapsed to a single #x20, and leading and trailing
        #x20's are removed.
        Note:  The notation #xA used here (and elsewhere in this
        specification) represents the Universal Character Set (UCS) code
        point hexadecimal A (line feed), which is denoted by U+000A.
        This notation is to be distinguished from &#xA;, which is the
        XML character reference to that same UCS code point.
    """
    ENUM = DataDict(
        preserve='preserve',
        replace='replace',
        colapse='colapse',
    )
    name = 'whiteSpace'
    def __init__(self, restriction):
        assert restriction in self.ENUM
        self.restriction = restriction

    def __call__(self, value):
        if self.restriction == self.ENUM.preserve:
            return value
        # Perform replace proccessing
        value = re.compile('(\t|\r|\n)').sub(' ', value)
        if self.restriction == self.ENUM.colapse:
            value = re.compile('\s+').sub(' ', value)
        return value

class totaldigits(Facet):
    """
    The totaldigits facet controls the maximum number of values in the value

    Note that it does not restrict the lexical space directly; a
    lexical representation that adds additional leading zero digits or
    trailing fractional zero digits is still permitted.
    """
    name = 'totalDigits'
    def __call__(self, value):
        """
        Restrict the total digets in the value space to those that can be
        represented lexically by the maximum of number digits provided by the
        restriction proprety
        """
        # totalDigits = 3
        # maximum value = 999
        # 999 = i X 10^-n
        # |i| < 10^totalDigits and 0 <= n <= totalDigits. 
        n = 10 % self.restriction
        maximum = pow(10, self.restriction) - n
        return value <= maximum


class fractiondigits(Facet):
    name = 'fractionDigits'
    def __call__(self, value):
        return True

class maxinclusive(Facet):
    name = 'maxInclusive'
    def __call__(self, value):
        return True

class maxexclusive(Facet):
    name = 'maxExclusive'
    def __call__(self, value):
        return True

class mininclusive(Facet):
    name = 'minInclusive'
    def __call__(self, value):
        return True

class minexclusive(Facet):
    name = 'minExclusive'
    def __call__(self, value):
        return True

class assertions(Facet):
    name = 'assertions'
    def __call__(self, value):
        return True

FACETS = DataDict({
    length.name : length,
    maxlength.name : maxlength,
    minlength.name : minlength,
    pattern.name : pattern,
    enumeration.name : enumeration,
    whitespace.name : whitespace,
    totaldigits.name : totaldigits,
    fractiondigits.name : fractiondigits,
    maxinclusive.name : maxinclusive,
    maxexclusive.name : maxexclusive,
    mininclusive.name : mininclusive,
    minexclusive.name : minexclusive,
})


class primative:
    # Primative methods
    @staticmethod
    def string(value):
        return value

    @staticmethod
    def boolean(value):
        if value in ['false', 'False', 'no']:
            return False
        if value in ['true', 'True', 'yes']:
            return True
        return value

    @staticmethod
    def decimal(value):
        try:
            return int(value)
        except ValueError:
            return float(value)

    @staticmethod
    def duration(value):
        return value

    @staticmethod
    def date(value, fmt='%Y-%m-%d'):
        # TODO: Value can have an optional timezone
        # see: http://www.w3.org/TR/xmlschema-2/#date
        return datetime.strptime(value, fmt)

    @staticmethod
    def time(value):
        return value

    @staticmethod
    def dateTime(value):
        return value

    @staticmethod
    def float_(value):
        return float(value)

    @staticmethod
    def hexBinary(value):
        return value

    @staticmethod
    def base64Binary(value):
        return value

    @staticmethod
    def anyURI(value):
        return value

    @staticmethod
    def NOTATION(value):
        return value

    @staticmethod
    def QName(value):
        return value


# ur-type definitions
anyType = ComplexTypeDef(
    name='anyType',
    targetns=XS,
    basedef=ITSELF,
    derivation='restriction',
    content_type=ContentType(
        variety=MIXED,
        partical=Partical(
            term=ModelGroup(
                SEQUENCE,
                particals=[
                    Partical(
                        WildCard(),
                        min_occurs=0,
                        max_occurs=UNBOUNDED,
                    )
                ]
            ),
            min_occurs=1,
            max_occurs=1,
        ),
    )
)

anySimpleType = SimpleTypeDef(
    name='anySimpleType',
    targetns=XS,
    basedef=anyType,
)

## Builtin Datatypes ##
# Builtin datatypes, both primative and derived, have a valid_facets property.
# Datatypes definded defined in schema documents derived from these types may
# use any valid facet in it's facets definitions.

## Primative Datatypes ##

# Primative datatypes are those that have anySimpleType as a base definition.

string = SimpleTypeDef(
    name='string',
    basedef=anySimpleType,
    primative=primative.string,
)
string._valid_facets = [
    length.name, minlength.name, maxlength.name, pattern.name, whitespace.name,
    enumeration.name,
]

boolean = SimpleTypeDef(
    name='boolean',
    basedef=anySimpleType,
    primative=primative.boolean
)
boolean._valid_facets = [
    pattern.name, whitespace.name
]

decimal = SimpleTypeDef(
    name='decimal',
    basedef=anySimpleType,
    primative=primative.decimal,
)
decimal._valid_facets = [
    totaldigits.name, fractiondigits.name, pattern.name, whitespace.name,
    enumeration.name, maxinclusive.name, maxexclusive.name, mininclusive.name,
    minexclusive.name,
]
date = SimpleTypeDef(
    name='date',
    facets=[],
    basedef=anySimpleType,
    primative=primative.date
)

base64binary = SimpleTypeDef(
    name='base64Binary',
    basedef=anySimpleType,
    primative=primative.date
)
base64binary._valid_facets = [
    length.name, minlength.name, maxlength.name, pattern.name,
    enumeration.name, assertions.name,
]
valid_facets = []

## Derived Datatypes ##

integer = SimpleTypeDef(
    name='integer',
    basedef=decimal,
)
integer._valid_facets = [
    totaldigits.name, fractiondigits.name, pattern.name, whitespace.name,
    enumeration.name, maxinclusive.name, maxexclusive.name, mininclusive.name,
    minexclusive.name,
]
nonnegativeint = SimpleTypeDef(
    name='nonNegativeInteger',
    basedef=integer,
)
# TODO: nonNegativeInteger has Facets with fixed values

positiveInteger = SimpleTypeDef(
    name = 'positiveInteger',
    #TODO: This basedef should be nonNegativeIntiger
    basedef=nonnegativeint,
)
positiveInteger._valid_facets=[
    totaldigits.name, fractiondigits.name, pattern.name, whitespace.name,
    enumeration.name, maxinclusive.name, maxexclusive.name, mininclusive.name,
    minexclusive.name,
]

BUILTINS = DataDict({
   anySimpleType.name: anySimpleType,
   string.name : string,
   boolean.name : boolean,
   decimal.name : decimal,
   integer.name : integer,
   date.name : date,
   positiveInteger.name : positiveInteger,
   base64binary.name : base64binary,
   nonnegativeint.name : nonnegativeint,
})

def resolve_builtin(name):
    return BUILTINS[name]

