# -*- coding: utf-8 -*-

from ehex import utils
from ehex.parser import model
from ehex import (
    AUX_MARKER,
    SNEG_PREFIX,
    DNEG_PREFIX,
    K_PREFIX,
    M_PREFIX,
    IN_ATOM,
    OUT_ATOM,
    INPUT_ATOM,
    PATH_ATOM,
    DOMAIN,
    SOLVED,
    KAHL_SEMANTICS,
)


def remove_prefix(name, prefix):
    if name.startswith(prefix):
        return name[len(prefix) :]
    return name


def aux_name(symbol, prefix=""):
    if prefix:
        prefix += "_"
    return "{}{}{}".format(
        AUX_MARKER, prefix.upper(), remove_prefix(symbol, AUX_MARKER)
    )


def atom(symbol, terms=None):
    terms = [*utils.flatten(terms)]
    return model.Atom(symbol=symbol, arguments=terms)


def aux_atom(symbol, terms=None, prefix=""):
    aux_symbol = aux_name(symbol, prefix=prefix)
    return atom(aux_symbol, terms)


def prefixed_atom(prefix):
    def partial(symbol, terms=None):
        return aux_atom(symbol, terms=terms, prefix=prefix)

    return partial


def named_atom(symbol):
    def partial(*terms):
        return aux_atom(symbol, terms=terms)

    return partial


sn_atom = prefixed_atom(SNEG_PREFIX)
not_atom = prefixed_atom(DNEG_PREFIX)
not_k_atom = prefixed_atom(K_PREFIX)
m_atom = prefixed_atom(M_PREFIX)
in_atom = named_atom(IN_ATOM)
out_atom = named_atom(OUT_ATOM)


def domain_atom(modal):
    atom_ = guessing_atom(modal)
    symbol = aux_name(atom_.symbol, prefix=DOMAIN)
    arguments = getattr(atom_, "arguments", None)
    return atom(symbol, arguments)


def variable(symbol):
    return model.VariableTerm(ast=symbol)


def aux_variable(symbol):
    symbol = "{}{}".format(AUX_MARKER.upper(), symbol)
    return variable(symbol)


def constraint(body):
    return model.Constraint(body=model.RuleBody(literals=[*body]))


def cautious_inspection(symbol, terms):
    input_name = aux_name(INPUT_ATOM)
    path_variable = aux_variable("path").ast
    return atom(
        "&hexCautious[file, {}, {}, {}]".format(path_variable, input_name, symbol),
        terms,
    )


def brave_inspection(symbol, terms):
    input_name = aux_name(INPUT_ATOM)
    path_variable = aux_variable("path").ast
    return atom(
        "&hexBrave[file, {}, {}, {}]".format(path_variable, input_name, symbol), terms
    )


def rule(head, body=None):
    return model.Rule(head=head, body=body or [])


def fact(literal):
    return rule(disjunction([literal]))


def disjunction(literals):
    return model.Disjunction(literals=[*literals])


def conjunction(literals):
    return model.Conjunction(literals=[*literals])


def not_(literal):
    return model.DefaultNegation(literal=literal)


def neg(atom_):
    return model.StrongNegation(atom=atom_)


def guessing_atom(modal, opposite=False):
    if isinstance(modal, model.DefaultNegation):
        modal = modal.literal
    op = modal.op
    if opposite:
        op = {"K": "M", "M": "K"}[op]
    if op == "K":
        return not_k_literal(modal.literal)
    if op == "M":
        return m_literal(modal.literal)
    assert False
    return None


def not_k_literal(literal):
    if isinstance(literal, model.StrongNegation):
        atom_ = sn_atom(literal.atom.symbol, literal.atom.arguments)
    else:
        atom_ = literal
    return not_k_atom(atom_.symbol, atom_.arguments)


def m_literal(literal):
    if isinstance(literal, model.StrongNegation):
        atom_ = sn_atom(literal.atom.symbol, literal.atom.arguments)
    else:
        atom_ = literal
    return m_atom(atom_.symbol, atom_.arguments)


def path_atom():
    return atom(aux_name(PATH_ATOM), aux_variable("path"))


def k_constraints(modal):
    symbol = modal.literal.symbol
    terms = modal.literal.arguments
    datom = domain_atom(modal)
    cautious = aux_atom("cautious_" + symbol, terms)
    yield rule(
        cautious,
        [datom, path_atom(), modal.literal, cautious_inspection(symbol, terms)],
    )
    modal_term = guessing_term(modal)
    yield constraint([datom, in_atom(modal_term), cautious])
    yield constraint([datom, out_atom(modal_term), not_(cautious)])


def m_constraints(modal):
    symbol = modal.literal.symbol
    terms = modal.literal.arguments
    datom = domain_atom(modal)
    brave = aux_atom("brave_" + symbol, terms)
    yield rule(brave, [datom, path_atom(), brave_inspection(symbol, terms)])
    modal_term = guessing_term(modal)
    yield constraint([datom, out_atom(modal_term), modal.literal])
    yield constraint([datom, in_atom(modal_term), not_(brave)])
    yield constraint([datom, out_atom(modal_term), brave])


def functional_term(symbol, terms=None):
    return model.FunctionalTerm(symbol=symbol, arguments=terms)


def guessing_term(modal, opposite=False):
    atom_ = guessing_atom(modal, opposite=opposite)
    arguments = getattr(atom_, "arguments", None)
    return functional_term(atom_.symbol, arguments)


def input_rules():
    input_name = aux_name(INPUT_ATOM)
    x = "X"
    in_x = in_atom(x)
    out_x = out_atom(x)
    rules = (
        (atom(input_name, [in_x.symbol, 1, x]), in_x),
        (atom(input_name, [out_x.symbol, 1, x]), out_x),
    )
    yield from (rule(head, body) for head, body in rules)


def level_constraint(level):
    elem = model.AggregateElement(terms="X", literals=[out_atom("X")],)
    count_fn = model.AggregateFunction(symbol="#count", elements=[elem])
    return constraint(
        [not_(model.AggregateRelation(aggregate=count_fn, right_op="=", right=level))]
    )


def check_subset_rules():
    def solved_atom(terms):
        name = aux_name(SOLVED)
        return atom(name, terms)

    def not_solved_atom(terms):
        name = aux_name(SOLVED, prefix=SNEG_PREFIX)
        return atom(name, terms)

    yield rule(
        not_solved_atom("Z"),
        [in_atom("X"), not_(solved_atom(["Z", "X"])), solved_atom(["Z", "_"])],
    )
    yield constraint([not_(not_solved_atom("Z")), solved_atom(["Z", "_"])])


def guessing_rules(modals, optimize_guessing):
    yield constraint([in_atom("X"), out_atom("X")])
    for modal in modals:
        datom = domain_atom(modal)
        yield rule(
            disjunction(
                [in_atom(guessing_term(modal)), out_atom(guessing_term(modal))]
            ),
            [datom],
        )
        if optimize_guessing:
            yield rule(
                in_atom(guessing_term(modal)),
                [out_atom(guessing_term(modal, opposite=True)), datom],
            )


def guessing_hints(modals, semantics):
    for modal in modals:
        if semantics is KAHL_SEMANTICS:
            not_l = not_atom(modal.literal.symbol, modal.literal.arguments)
            m_condition = not_(not_l)
        else:
            m_condition = modal.literal
        condition = {
            "K": not_(modal.literal),
            "M": m_condition,
        }
        datom = domain_atom(modal)
        yield rule(in_atom(guessing_term(modal)), [condition[modal.op], datom])


def _checking_rules(modals):
    constraints = {
        "K": k_constraints,
        "M": m_constraints,
    }
    for modal in modals:
        yield from constraints[modal.op](modal)


def domain_facts(ground_modals):
    for modal in ground_modals:
        yield fact(domain_atom(modal))


def checking_rules(modals, path):
    yield fact(atom(aux_name(PATH_ATOM), '"{}"'.format(path)))
    yield from input_rules()
    yield from _checking_rules(modals)


def guessing_assignment_rules(modals, semantics):
    for modal in modals:
        literal = modal.literal
        head = guessing_atom(modal)
        in_guess = in_atom(guessing_term(modal))
        out_guess = out_atom(guessing_term(modal))
        yield rule(head, in_guess)
        if modal.op == "K":
            yield rule(head, [out_guess, not_(literal)])
        elif modal.op == "M":
            if semantics is KAHL_SEMANTICS:
                not_l = not_atom(literal.symbol, literal.arguments)
                yield rule(head, [out_guess, not_(not_l)])
                yield rule(not_l, [out_guess, not_(literal)])
            else:
                yield rule(head, [out_guess, literal])
        else:
            assert False
