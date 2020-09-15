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
            contrary_modal = model.clone_literal(
                modal, literal=model.opposite(modal.literal)
            )
            yield elpmodel.Rule(
                head=guess, body=[neg_guess.clone(args=[contrary_modal]), gnd]
            )


def facts(atoms):
    for atom in atoms:
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
            not_auxc = elpmodel.StandardLiteral(negation="not", atom=auxc)

            yield elpmodel.Rule(head=auxc, body=[gnd, atom, hexc])
            yield elpmodel.Rule(head=None, body=[gnd, guess, auxc])
            yield elpmodel.Rule(head=None, body=[gnd, neg_guess, not_auxc])
        else:
            hexb = hexmodel.HEXBraveAtom(program=program, query=atom)
            auxb = auxmodel.AuxBrave(args=[atom])
            not_auxb = elpmodel.StandardLiteral(negation="not", atom=auxb)

            yield elpmodel.Rule(head=auxb, body=[gnd, hexb])
            yield elpmodel.Rule(head=None, body=[gnd, guess, not_auxb])
            yield elpmodel.Rule(head=None, body=[gnd, neg_guess, auxb])


def cardinality_check(guess_size):
    atom = auxmodel.AuxGuess(args=["M"])
    element = elpmodel.AggregateElement(terms=["M"], literals=[atom])
    count = elpmodel.AggregateAtom(
        name="#count",
        elements=[element],
        right_rel="=",
        right=guess_size,
    )
    not_count = elpmodel.StandardLiteral(negation="not", atom=count)
    yield elpmodel.Rule(head=None, body=[not_count])


def subset_check():
    guess = auxmodel.AuxGuess(args=["M"])
    member = auxmodel.AuxMember(args=["_", "S"])
    not_member = elpmodel.StandardLiteral(
        negation="not", atom=member.clone(args=["M", "S"])
    )
    element = elpmodel.AggregateElement(
        terms=["M"], literals=[guess, not_member]
    )
    count = elpmodel.AggregateAtom(
        name="#count",
        elements=[element],
        right_rel="=",
        right=0,
    )
    yield elpmodel.Rule(head=None, body=[count, member])


def member_rules(omega):
    for j, guess in enumerate(omega):
        atoms = [
            auxmodel.AuxMember(args=[atom.args[0], f"world{j+1}"])
            for atom in guess
        ]
        yield from facts(atoms)


def negation_constraints(keys):
    for name, arity in keys:
        args = [f"X{i+1}" for i in range(arity)]
        atom = elpmodel.Atom(name=name, args=args)
        natom = model.clone_atom(atom, negation="-")
        yield elpmodel.Rule(head=None, body=[atom, natom])


def planning_mode_guessing_rules():
    goal_atom = elpmodel.Atom(name="goal", args=[])
    modal1 = elpmodel.ModalLiteral(
        modality="M",
        literal=elpmodel.StandardLiteral(atom=goal_atom, negation="not"),
    )
    modal2 = elpmodel.ModalLiteral(
        modality="M", literal=elpmodel.StandardLiteral(atom=goal_atom)
    )
    yield from facts(
        [
            auxmodel.AuxGuess(args=[modal1], negation="-"),
            auxmodel.AuxGuess(args=[modal2]),
        ]
    )
