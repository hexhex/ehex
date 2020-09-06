from ehex.utils import model
from ehex.parser.models import elpmodel

PREFIX = "z_"
NEG_NAME = "Neg"
NAF_NAME = "Not"


class AuxAtom(elpmodel.Atom):
    args = []
    negation = None
    style = None
    _name = None

    def clone(self, **kws):
        return model.clone_atom(self, **kws)

    def opposite(self):
        return model.opposite(self)


class AuxGuess(AuxAtom):
    _name = "G"
    name = PREFIX + _name


class AuxMember(AuxAtom):
    _name = "Member"
    name = PREFIX + _name


class AuxInput(AuxAtom):
    _name = "Input"
    name = PREFIX + _name


class AuxTrue(AuxAtom):
    _name = "True"
    style = "flat"
    name = PREFIX + _name


class AuxGround(AuxAtom):
    _name = "Gnd"
    style = "flat"
    name = PREFIX + _name


class AuxBrave(AuxAtom):
    _name = "Brave"
    style = "flat"
    name = PREFIX + _name


class AuxCautious(AuxAtom):
    _name = "Cautious"
    style = "flat"
    name = PREFIX + _name
