import sys

from ehex.utils import model
from ehex.codegen import elpgen
from ehex.codegen import auxgen
from ehex.codegen import rules
from ehex.parser.models import elpmodel
from ehex.parser.models import auxmodel

THIS_MODULE = sys.modules[__name__]

# The generic reduct generator implements the following transformation
# rules, where α is an atom, true(φ) is an auxiliary atom over a modal
# literal φ, and guess(ρ) and ¬guess(ρ) are auxiliary atoms over a weak
# modal literal ρ:
#
#      Modal literal   Replace with    Add rules
#     ──────────────────────────────────────────────────────────────────
#      M α             true(M α)     │ {true(M α) ← guess(M α);
#      K not α         not true(M α) │  true(M α) ← α, ¬guess(M α)}
#     ──────────────────────────────────────────────────────────────────
#      K α             true(K α)     │ {true(K α) ← α, ¬guess(M not α)}
#      M not α         not true(K α) │


class GenericReductGenerator(auxgen.ELPAuxGenerator):
    def __init__(self):
        super().__init__(modules=[elpgen, auxgen, THIS_MODULE])
        self.aux_true_keys = set()


class Program(auxgen.Program):
    def __init__(self, *args, **kws):
        super().__init__(*args, **kws)
        self.context.aux_true_keys.clear()


class Rule(elpgen.Rule):
    def render_fields(self, fields):
        body = [
            self.replace_modal(literal)
            if isinstance(literal, elpmodel.ModalLiteral)
            else literal
            for literal in fields["body"]
        ]
        fields.update(body=body)
        return super().render_fields(fields)

    def replace_modal(self, modal):
        modality = modal.modality
        literal = modal.literal
        true_modal = modal
        if modality == "M" and not literal.negation:
            repl = elpmodel.StandardLiteral(
                atom=auxmodel.AuxTrue(args=[true_modal])
            )
        elif modality == "K" and literal.negation:
            true_modal = model.opposite(modal)
            repl = elpmodel.StandardLiteral(
                atom=auxmodel.AuxTrue(args=[true_modal]), negation="not"
            )
        elif modality == "K" and not literal.negation:
            repl = elpmodel.StandardLiteral(
                atom=auxmodel.AuxTrue(args=[true_modal])
            )
        elif modality == "M" and literal.negation:
            true_modal = model.opposite(modal)
            repl = elpmodel.StandardLiteral(
                atom=auxmodel.AuxTrue(args=[true_modal]), negation="not"
            )
        key = model.key(true_modal)
        if key not in self.context.aux_true_keys:
            self.context.aux_true_keys.add(key)
            self.context.aux_rules.extend(rules.reduct_true(repl.atom))
        return repl
