from ehex.codegen import rules
from ehex.parser.models import auxmodel, elpmodel
from ehex.utils import model

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


def generic_reduct(elp, semantics=None):
    aux_true_keys = set()

    for rule in elp.rules:
        modals = [
            element
            for element in rule.body
            if isinstance(element, elpmodel.ModalLiteral)
        ]

        if not modals:
            yield rule
            continue

        body = dict(transform_body(rule.body))
        yield elpmodel.Rule(head=rule.head, body=list(body.values()))

        for modal in modals:
            repl = body[modal]
            key = model.key(model.weak_form(modal))
            if key not in aux_true_keys:
                aux_true_keys.add(key)
                yield from replacement_rules(repl.atom, semantics=semantics)


def transform_body(body):
    for element in body:
        if not isinstance(element, elpmodel.ModalLiteral):
            yield (element, element)
            continue
        mtype = (element.modality, not element.literal.negation)
        true_modal = element
        if mtype == ("M", True):
            repl = elpmodel.StandardLiteral(
                atom=auxmodel.AuxTrue(args=[true_modal])
            )
        elif mtype == ("K", False):
            true_modal = model.opposite(element)
            repl = elpmodel.StandardLiteral(
                atom=auxmodel.AuxTrue(args=[true_modal]), negation="not"
            )
        elif mtype == ("K", True):
            repl = elpmodel.StandardLiteral(
                atom=auxmodel.AuxTrue(args=[true_modal])
            )
        elif mtype == ("M", False):
            true_modal = model.opposite(element)
            repl = elpmodel.StandardLiteral(
                atom=auxmodel.AuxTrue(args=[true_modal]), negation="not"
            )
        yield (element, repl)


def replacement_rules(repl, semantics=None):
    modal = model.clone_literal(repl.args[0])
    repl = repl.clone(args=[modal])
    atom = modal.literal.atom
    atom.args = [f"T{i+1}" for i in range(len(atom.args))]
    weak_modal = model.weak_form(modal)
    guess = auxmodel.AuxGuess(args=[weak_modal])
    neg_guess = guess.opposite()

    if modal.modality == "M":
        yield elpmodel.Rule(head=repl, body=[guess])
        if semantics == "NEX" and not modal.literal.negation:
            aux_not_atom = auxmodel.AuxLiteral(atom=atom, negation="not")
            not_aux_not_atom = elpmodel.StandardLiteral(
                atom=aux_not_atom, negation="not"
            )
            not_atom = elpmodel.StandardLiteral(atom=atom, negation="not")
            yield elpmodel.Rule(head=repl, body=[not_aux_not_atom, neg_guess])
            yield elpmodel.Rule(head=aux_not_atom, body=[not_atom, neg_guess])
        else:
            yield elpmodel.Rule(head=repl, body=[atom, neg_guess])
    if modal.modality == "K":
        yield elpmodel.Rule(head=repl, body=[atom, neg_guess])


def optimized_replacement_rules(guess_facts):
    for atom in guess_facts:
        modal = atom.args[0]
        literal = modal.literal
        if atom.negation:
            if literal.negation:
                # for ¬guess(M not α) yield true(K α) ← α.
                repl = auxmodel.AuxTrue(args=[model.opposite(modal)])
            else:
                # for ¬guess(M α) yield true(M α) ← α.
                repl = auxmodel.AuxTrue(args=[modal])
            yield elpmodel.Rule(head=repl, body=[literal.atom])
        elif not literal.negation:
            # for guess(M α) yield true(M α).
            repl = auxmodel.AuxTrue(args=[modal])
            yield elpmodel.Rule(head=repl, body=[])
