from dataclasses import dataclass, field
from typing import Any

from ehex.parser.models import elpmodel
from ehex.utils import model

PREFIX = "z_"
NEG_NAME = "Neg"
NAF_NAME = "Not"


@dataclass(eq=False)
class AuxAtom(elpmodel.Atom):
    args: list = field(default_factory=list)
    negation: Any = None
    style: Any = None
    _name = None

    def clone(self, **kws):
        return model.clone_atom(self, **kws)

    def opposite(self):
        return model.opposite(self)


@dataclass(eq=False)
class AuxGuess(AuxAtom):
    _name = "G"
    name: Any = PREFIX + _name


@dataclass(eq=False)
class AuxMember(AuxAtom):
    _name = "Member"
    name: Any = PREFIX + _name


@dataclass(eq=False)
class AuxInput(AuxAtom):
    _name = "Input"
    name: Any = PREFIX + _name


@dataclass(eq=False)
class AuxTrue(AuxAtom):
    _name = "True"
    style: Any = "flat"
    name: Any = PREFIX + _name


@dataclass(eq=False)
class AuxGround(AuxAtom):
    _name = "Gnd"
    style: Any = "flat"
    name: Any = PREFIX + _name


@dataclass(eq=False)
class AuxBrave(AuxAtom):
    _name = "Brave"
    style: Any = "flat"
    name: Any = PREFIX + _name


@dataclass(eq=False)
class AuxCautious(AuxAtom):
    _name = "Cautious"
    style: Any = "flat"
    name: Any = PREFIX + _name


@dataclass(eq=False)
class AuxLiteral(elpmodel.StandardLiteral):
    pass
