from dataclasses import dataclass
from typing import Any

from tatsu.objectmodel import Node

from ehex.parser.models import auxmodel


@dataclass(eq=False)
class HEXExternalAtom(Node):
    name: Any = None
    in_args: Any = None
    out_args: Any = None


@dataclass(eq=False)
class HEXReasoningAtom(HEXExternalAtom):
    program_type: Any = "file"
    program: Any = None
    input_name: Any = auxmodel.PREFIX + auxmodel.AuxInput._name
    query: Any = None


@dataclass(eq=False)
class HEXBraveAtom(HEXReasoningAtom):
    name: Any = "&hexBrave"


@dataclass(eq=False)
class HEXCautiousAtom(HEXReasoningAtom):
    name :Any= "&hexCautious"
