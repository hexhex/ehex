from ehex.parser.models import elpmodel
from ehex.parser.models import auxmodel
from ehex.parser.models import hexmodel
from ehex.utils import model


def guessing_rules(ground_atoms):
    for gnd in ground_atoms:
        guess = gnd.clone(model=auxmodel.AuxGuess)
        neg_guess = guess.clone(negation="-")
        head = elpmodel.Disjunction(atoms=[guess, neg_guess])
        yield elpmodel.Rule(head=head, body=[gnd])


def facts(atoms):
    for atom in atoms:
        yield elpmodel.Rule(head=atom, body=[])


def input_rules():
    guess = auxmodel.AuxGuess(args=["M"])
    neg_guess = guess.clone(negation="-")
    yield elpmodel.Rule(
        head=auxmodel.AuxInput(args=[guess.clone(args=[]), 1, "M"]),
        body=[guess],
    )
    yield elpmodel.Rule(
        head=auxmodel.AuxInput(
            args=[neg_guess.clone(args=[], no_constraint=True), 1, "M"]
        ),
        body=[neg_guess],
    )


def checking_rules(ground_atoms, reduct_out):
    seen = set()
    program = f'"{reduct_out}"'
    for gnd in ground_atoms:
        modal = gnd.args[0]
        if modal.modality == "K":
            raise ValueError(f"modality is {modal.modality}, expected M")

        key = model.key(modal)
        if key in seen:
            continue
        seen.add(key)

        modal = model.clone_literal(modal)
        atom = modal.literal.atom
        atom.args = [f"T{i+1}" for i in range(len(atom.args))]
        gnd = gnd.clone(args=[modal])
        guess = gnd.clone(model=auxmodel.AuxGuess)
        neg_guess = guess.clone(negation="-")

        if modal.literal.negation:
            hexc = hexmodel.HEXCautiousAtom(program=program, query=atom)
            auxc = auxmodel.AuxCautious(args=[atom])
            naf_auxc = elpmodel.StandardLiteral(negation="not", atom=auxc)

            yield elpmodel.Rule(head=auxc, body=[gnd, atom, hexc])
            yield elpmodel.Rule(head=None, body=[guess, auxc])
            yield elpmodel.Rule(head=None, body=[neg_guess, naf_auxc])
        else:
            hexb = hexmodel.HEXBraveAtom(program=program, query=atom)
            auxb = auxmodel.AuxBrave(args=[atom])
            nauf_auxb = elpmodel.StandardLiteral(negation="not", atom=auxb)
            naf_atom = elpmodel.StandardLiteral(negation="not", atom=atom)

            yield elpmodel.Rule(head=auxb, body=[gnd, naf_atom, hexb])
            yield elpmodel.Rule(head=auxb, body=[atom])
            yield elpmodel.Rule(head=None, body=[guess, nauf_auxb])
            yield elpmodel.Rule(head=None, body=[neg_guess, auxb])


def cardinality_check(level):
    atom = auxmodel.AuxGuess(args=["M"])
    element = elpmodel.AggregateElement(terms=["M"], literals=[atom])
    count = elpmodel.AggregateAtom(
        name="#count", elements=[element], right_rel="=", right=level,
    )
    naf_count = elpmodel.StandardLiteral(negation="not", atom=count)
    yield elpmodel.Rule(head=None, body=[naf_count])


def subset_check(level):
    guess = auxmodel.AuxGuess(args=["M"])
    member = auxmodel.AuxMember(args=["_", "S"])
    naf_member = elpmodel.StandardLiteral(
        negation="not", atom=member.clone(args=["M", "S"])
    )
    element = elpmodel.AggregateElement(
        terms=["M"], literals=[guess, naf_member]
    )
    count = elpmodel.AggregateAtom(
        name="#count", elements=[element], right_rel="=", right=0,
    )
    yield elpmodel.Rule(head=None, body=[count, member])


def member_facts(omega):
    for j, guess in enumerate(omega):
        k = len(guess)
        for modal in guess:
            name = f'"world{j+1}@{k}"'
            yield elpmodel.Rule(
                head=auxmodel.AuxMember(args=[modal, name]), body=[]
            )


def reduct_true(aux_true):
    modal = model.clone_literal(aux_true.args[0])
    aux_true = aux_true.clone(args=[modal])
    atom = modal.literal.atom
    atom.args = [f"T{i+1}" for i in range(len(atom.args))]
    weak_modal = model.weak_form(modal)
    guess = auxmodel.AuxGuess(args=[weak_modal])
    neg_guess = guess.opposite()

    if modal.modality == "M":
        yield elpmodel.Rule(head=aux_true, body=[guess])
        yield elpmodel.Rule(head=aux_true, body=[atom, neg_guess])
    if modal.modality == "K":
        yield elpmodel.Rule(head=aux_true, body=[atom, neg_guess])
