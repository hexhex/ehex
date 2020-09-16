from ehex.codegen import render
from ehex.parser import asparser, aspif
from ehex.parser.models import auxmodel
from ehex.solver import clingo
from ehex.solver.config import cfg
from ehex.utils import model, solver


def compute_consequences(elp, facts, context=None):
    opt_consq_src = render.enum_program(elp, facts, context=context)

    if context:
        opt_consq_out = cfg.path.opt_consq_out.with_suffix(
            f".{context.level}.lp"
        )
    else:
        opt_consq_out = cfg.path.opt_consq_out

    def tokenize_next(result):
        return asparser.tokenize(next(result))

    kws = {
        "solver": clingo,
        "src": opt_consq_src,
        "out": opt_consq_out,
        "project": "show",
        "parse": tokenize_next,
    }

    try:
        brave_keys = solver.solve(enum_mode="brave", **kws)
        cautious_keys = solver.solve(enum_mode="cautious", **kws)
    except StopIteration:
        raise solver.Unsatisfiable

    return brave_keys, cautious_keys


def with_consequences(elp, facts, context=None):
    brave_keys, cautious_keys = compute_consequences(
        elp, facts, context=context
    )
    gnd_remove, guess_true, guess_false = [], [], []

    for gnd in facts.ground:
        literal = gnd.args[0].literal
        name = literal.atom.name
        if literal.atom.negation:
            name = model.neg_name(name)
        args = gnd.token[1]
        key = (name, args)

        guess_fact = None
        if key not in brave_keys:
            negation = None if literal.negation else "-"
            guess_fact = gnd.clone(model=auxmodel.AuxGuess, negation=negation)
        elif key in cautious_keys:
            negation = "-" if literal.negation else None
            guess_fact = gnd.clone(model=auxmodel.AuxGuess, negation=negation)
        if guess_fact:
            if negation:
                guess_false.append(guess_fact)
            else:
                guess_true.append(guess_fact)
            guess_fact.token = gnd.token
            gnd_remove.append(gnd)

    if gnd_remove:
        ground_facts = facts.ground.difference(gnd_remove)

        if context:
            k_min = len(guess_true)
            k_max = len(ground_facts) + k_min
            if not k_min <= context.guess_size <= k_max:
                raise solver.Unsatisfiable

        guesses = {g.token: g for g in facts.guess}
        guess_remove = [
            guess for gnd in gnd_remove if (guess := guesses.get(gnd.token))
        ]

        replace = {"ground": ground_facts}
        if guess_remove:
            replace["guess"] = facts.guess.difference(guess_remove)
        if guess_true:
            replace["guess_true"] = facts.guess_true.union(guess_true)
        if guess_false:
            replace["guess_false"] = facts.guess_false.union(guess_false)
        facts = facts._replace(**replace)

        if context and guess_true:
            facts = facts._replace(guess=facts.guess.union(guess_true))

    return facts


def ground_reduct(elp, facts):
    opt_reduct_src = render.grounding_program(elp, facts)
    result = solver.solve(
        clingo,
        opt_reduct_src,
        out=cfg.path.opt_reduct_out,
        parse=aspif.parse,
        mode="gringo",
        output="intermediate",
    )

    def effective_atoms(stream):
        body_keys = set()
        fact_atoms = set()
        symbols = dict()
        for stype, data in stream:
            if stype == aspif.RULE:
                _, (_, body) = data
                body_keys.update(abs(b) for b in body)
            if stype == aspif.OUTPUT:
                symbol, condition = data
                if condition:
                    symbols.update(dict.fromkeys(condition, symbol))
                else:
                    fact_atoms.add(symbol)
        return (
            fact_atoms,
            set(symbols[key] for key in body_keys & symbols.keys()),
        )

    def keys(symbols):
        aux_name = auxmodel.AuxTrue.name
        text = ",".join(
            [s[len(aux_name) + 1 :] for s in symbols if s.startswith(aux_name)]
        )
        return asparser.tokenize(text)

    fact_atoms, body_atoms = effective_atoms(result)
    return set(keys(fact_atoms)), set(keys(body_atoms))


def with_reduct(elp, facts):
    fact_keys, body_keys = ground_reduct(elp, facts)

    def mkey(atom):
        token = atom.token
        gnd_name = auxmodel.AuxGround.name
        if token[0].startswith(gnd_name):
            name, args = token
            name = name[len(gnd_name) + 1 :]
        else:
            token = token[1][0]
            if isinstance(token, str):
                token = token, ()
            name, args = token
            name = name[len(auxmodel.PREFIX) :]
        name = name.replace(f"M_{auxmodel.NAF_NAME}_", "K_", 1)
        return (name, args)

    replace = {}
    for field, _atoms in facts._asdict().items():
        remove = []

        for atom in _atoms:
            if mkey(atom) not in fact_keys | body_keys:
                remove.append(atom)

        if remove:
            replace[field] = _atoms.difference(remove)

    return facts._replace(**replace)


def with_goal(facts):
    gnd_goal_facts = [
        g for g in facts.ground if g.args[0].literal.atom.name == "goal"
    ]
    guess_goal_facts = []

    for gnd in gnd_goal_facts:
        negation = "-" if gnd.args[0].literal.negation else None
        guess = gnd.clone(model=auxmodel.AuxGuess, negation=negation)
        guess.token = gnd.token
        guess_goal_facts.append(guess)

    return facts._replace(guess=facts.guess.union(guess_goal_facts))
