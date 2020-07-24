from tatsu.objectmodel import Node

from ehex.parser.models import auxmodel


class HEXExternalAtom(Node):
    name = None
    in_args = None
    out_args = None


class HEXReasoningAtom(HEXExternalAtom):
    program_type = "file"
    program = None
    input_name = auxmodel.PREFIX + auxmodel.AuxInput._name
    query = None


class HEXBraveAtom(HEXReasoningAtom):
    name = "&hexBrave"


class HEXCautiousAtom(HEXReasoningAtom):
    name = "&hexCautious"
