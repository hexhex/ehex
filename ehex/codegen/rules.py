from ehex.parser.models import auxmodel, elpmodel, hexmodel
from ehex.utils import model


def guessing_rules(ground_facts, guessing_hints=False):
    seen = set()
    for gnd in ground_facts:
        key = model.key(gnd.args[0])
        if key in seen:
            continue
        seen.add(key)
        modal = model.clone_literal(gnd.args[0])
        atom = modal.literal.atom
        atom.args = [f"T{i+1}" for i in range(len(atom.args))]
        gnd = gnd.clone(args=[modal])
        guess = gnd.clone(model=auxmodel.AuxGuess)
        neg_guess = guess.clone(negation="-")
        head = elpmodel.Disjunction(atoms=[guess, neg_guess])
        yield elpmodel.Rule(head=head, body=[gnd])
        if guessing_hints:
            yield elpmodel.Rule(head=guess, body=[modal.literal, gnd])


def fact_rules(facts):
    for atom in facts:
        yield elpmodel.Rule(head=atom, body=[])


def input_rules():
    guess = auxmodel.AuxGuess(args=["M"])
    neg_guess = guess.clone(negation="-", no_constraint=True)
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
        neg_guess = guess.clone(negation="-", no_constraint=True)

        if modal.literal.negation:
            hexc = hexmodel.HEXCautiousAtom(program=program, query=atom)
            auxc = auxmodel.AuxCautious(args=[atom])
            naf_auxc = elpmodel.StandardLiteral(negation="not", atom=auxc)

            yield elpmodel.Rule(head=auxc, body=[gnd, atom, hexc])
            yield elpmodel.Rule(head=None, body=[gnd, guess, auxc])
            yield elpmodel.Rule(head=None, body=[gnd, neg_guess, naf_auxc])
        else:
            hexb = hexmodel.HEXBraveAtom(program=program, query=atom)
            auxb = auxmodel.AuxBrave(args=[atom])
            nauf_auxb = elpmodel.StandardLiteral(negation="not", atom=auxb)
            naf_atom = elpmodel.StandardLiteral(negation="not", atom=atom)

            yield elpmodel.Rule(head=auxb, body=[gnd, naf_atom, hexb])
            yield elpmodel.Rule(head=auxb, body=[gnd, atom])
            yield elpmodel.Rule(head=None, body=[gnd, guess, nauf_auxb])
            yield elpmodel.Rule(head=None, body=[gnd, neg_guess, auxb])


def cardinality_check(guess_size):
    atom = auxmodel.AuxGuess(args=["M"])
    element = elpmodel.AggregateElement(terms=["M"], literals=[atom])
    count = elpmodel.AggregateAtom(
        name="#count", elements=[element], right_rel="=", right=guess_size,
    )
    naf_count = elpmodel.StandardLiteral(negation="not", atom=count)
    yield elpmodel.Rule(head=None, body=[naf_count])


def subset_check():
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


def member_rules(omega):
    for j, guess in enumerate(omega):
        atoms = [
            auxmodel.AuxMember(args=[atom.args[0], f"world{j+1}"])
            for atom in guess
        ]
        yield from fact_rules(atoms)


def replacement_rules(repl):
    modal = model.clone_literal(repl.args[0])
    repl = repl.clone(args=[modal])
    atom = modal.literal.atom
    atom.args = [f"T{i+1}" for i in range(len(atom.args))]
    weak_modal = model.weak_form(modal)
    guess = auxmodel.AuxGuess(args=[weak_modal])
    neg_guess = guess.opposite()

    if modal.modality == "M":
        yield elpmodel.Rule(head=repl, body=[guess])
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
