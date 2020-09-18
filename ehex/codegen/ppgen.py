import sys

from ehex.codegen import auxgen, elpgen
from ehex.parser.models import auxmodel, elpmodel
from ehex.utils import model

THIS_MODULE = sys.modules[__name__]


class PositiveProgramGenerator(auxgen.ELPAuxGenerator):
    def __init__(self):
        super().__init__(modules=[elpgen, auxgen, THIS_MODULE])


def positive_program(elp):
    gnd_rules = []

    for rule in elp.rules:
        modals = [
            literal
            for literal in rule.body
            if isinstance(literal, elpmodel.ModalLiteral)
        ]
        body = list(positive_literals(rule.body))
        gnd_rules += grounding_rules(modals, body)

        if not rule.head:
            continue

        if isinstance(rule.head, elpmodel.Disjunction):
            for atom in rule.head.atoms:
                yield elpmodel.Rule(head=atom, body=body)
            continue

        if isinstance(rule.head, elpmodel.ChoiceAtom):
            for element in rule.head.elements:
                yield elpmodel.Rule(
                    head=element.atom, body=body + element.literals
                )
            continue

        yield elpmodel.Rule(head=rule.head, body=body)

    yield from gnd_rules


def positive_literals(literals):
    for literal in literals:
        if literal.negation:
            continue
        if isinstance(literal, elpmodel.ModalLiteral):
            if literal.modality == "K" and not literal.literal.negation:
                yield literal.literal
            continue
        if isinstance(literal, elpmodel.AggregateLiteral) and "=" not in (
            literal.atom.left_rel,
            literal.atom.right_rel,
        ):
            continue
        if (
            isinstance(literal.atom, elpmodel.BuiltinAtom)
            and literal.atom.rel != "="
        ):
            continue
        yield literal


def grounding_rules(modals, body):
    for modal in modals:
        head = auxmodel.AuxGround(args=[model.weak_form(modal)])
        yield elpmodel.Rule(head=head, body=body)
