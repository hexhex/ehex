import sys

from ehex.codegen import auxgen, elpgen
from ehex.parser.models import auxmodel, elpmodel
from ehex.utils import model

THIS_MODULE = sys.modules[__name__]


class PositiveProgramGenerator(auxgen.ELPAuxGenerator):
    def __init__(self):
        super().__init__(modules=[elpgen, auxgen, THIS_MODULE])


class Program(auxgen.Program):
    def __init__(self, *args, **kws):
        super().__init__(*args, **kws)
        self.context.aux_rules.clear()

    def render_fields(self, fields):
        rules = list(self.transform_rules(fields["rules"]))
        rules += self.context.aux_rules
        fields.update(rules=rules)

    def transform_rules(self, rules):
        for rule in rules:
            head = rule.head
            modals = [
                literal
                for literal in rule.body
                if isinstance(literal, elpmodel.ModalLiteral)
            ]
            body = list(self.positive_literals(rule.body))
            self.context.aux_rules += self.grounding_rules(modals, body)
            if not head:
                continue
            if isinstance(head, elpmodel.Disjunction):
                for atom in head.atoms:
                    yield elpmodel.Rule(head=atom, body=body)
                continue
            if isinstance(head, elpmodel.ChoiceAtom):
                for element in head.elements:
                    yield elpmodel.Rule(
                        head=element.atom, body=body + element.literals
                    )
                continue
            yield rule

    @staticmethod
    def grounding_rules(modals, body):
        weak_modals = [model.weak_form(modal) for modal in modals]
        for modal in weak_modals:
            head = auxmodel.AuxGround(args=[modal])
            yield elpmodel.Rule(head=head, body=body)

    @staticmethod
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
