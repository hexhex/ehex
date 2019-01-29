# -*- coding: utf-8 -*-

from ehex.parser import model
from ehex.filter import Terms
from ehex import utils
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
    EPISTEMIC_NEGATION,
    DOMAIN,
    SOLVED,
    KAHL_SEMANTICS,
    SE_SEMANTICS,
)


def remove_prefix(name, prefix):
    if name.startswith(prefix):
        return name[len(prefix):]
    return name


def aux_name(symbol, prefix=''):
    if prefix:
        prefix += '_'
    return '{}{}{}'.format(
        AUX_MARKER, prefix.upper(), remove_prefix(symbol, AUX_MARKER)
    )


def atom(symbol, terms=None):
    terms = list(utils.flatten(terms))
    return model.Atom(symbol=symbol, arguments=terms)


def aux_atom(symbol, terms=None, prefix=''):
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
eneg_atom = named_atom(EPISTEMIC_NEGATION)
domain_atom = named_atom(DOMAIN)
in_atom = named_atom(IN_ATOM)
out_atom = named_atom(OUT_ATOM)


def modal_domain_atom(op, symbol, terms):
    return atom('{}_{}_{}'.format(aux_name(DOMAIN), op, symbol), terms)


def program(statements=None):
    return model.Program(statements=list(statements or []))


def variable(symbol):
    return model.VariableTerm(ast=symbol)


def aux_variable(symbol):  # TODO: review usage
    return variable('AUX__' + symbol)


def constraint(body):
    return model.Constraint(body=body)


def cautious_inspection(symbol, terms):
    input_name = aux_name(INPUT_ATOM)
    path_variable = aux_variable('path').ast
    return atom(
        '&hexCautious[file, {}, {}, {}]'.format(
            path_variable, input_name, symbol
        ), terms
    )


def brave_inspection(symbol, terms):
    input_name = aux_name(INPUT_ATOM)
    path_variable = aux_variable('path').ast
    return atom(
        '&hexBrave[file, {}, {}, {}]'.format(
            path_variable, input_name, symbol
        ), terms
    )


def rule(head, body=None):
    return model.Rule(head=head, body=body or [])


def fact(literal):
    return rule(literal)


def disjunction(literals):
    return model.Disjunction(literals=list(literals))


def conjunction(literals):
    return model.Conjunction(literals=list(literals))


def not_(literal):
    return model.DefaultNegation(literal=literal)


def neg(atom_):
    return model.StrongNegation(atom=atom_)


def modal_to_literal(modal, switch_mode=False):
    if isinstance(modal, model.DefaultNegation):
        modal = modal.literal
    op = modal.op
    if switch_mode:
        op = {'K': 'M', 'M': 'K'}[op]
    if op == 'K':
        return not_k_literal(modal.literal)
    elif op == 'M':
        return m_literal(modal.literal)
    assert False


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
    return atom(aux_name(PATH_ATOM), aux_variable('path'))


def k_constraints(modal):
    term = guess_term(modal)
    symbol = modal.literal.symbol
    terms = [term for term in Terms(modal)]
    datom = modal_domain_atom('k', symbol, terms)
    not_cautious = not_atom('cautious_' + symbol, terms)
    yield rule(
        not_cautious, [
            datom,
            path_atom(),
            not_(cautious_inspection(symbol, terms)),
        ]
    )
    yield rule(not_cautious, [datom, not_(modal.literal)])
    yield constraint([datom, in_atom(term), not_(not_cautious)])
    yield constraint([datom, out_atom(term), not_cautious])


def m_constraints(modal):
    term = guess_term(modal)
    symbol = modal.literal.symbol
    terms = [term for term in Terms(modal)]
    datom = modal_domain_atom('m', symbol, terms)
    brave = aux_atom('brave_' + symbol, terms)
    yield rule(brave, [datom, path_atom(), brave_inspection(symbol, terms)])
    yield rule(brave, [datom, modal.literal])
    yield constraint([datom, in_atom(term), not_(brave)])
    yield constraint([datom, out_atom(term), brave])


def functional_term(symbol, terms=None):
    return model.FunctionalTerm(symbol=symbol, arguments=terms)


def guess_term(modal):
    literal = modal_to_literal(modal)
    arguments = getattr(literal, 'arguments', None)
    return functional_term(literal.symbol, arguments)


def input_rules():
    input_name = aux_name(INPUT_ATOM)
    in_name = aux_name(IN_ATOM)
    out_name = aux_name(OUT_ATOM)
    rules = (
        (atom(input_name, [in_name, 1, 'X']), in_atom('X')),
        (atom(input_name, [out_name, 1, 'X']), out_atom('X')),
    )
    yield from (rule(head, body) for head, body in rules)


def level_constraint(level):
    elem = model.AggregateElement(
        terms='X',
        literals=[out_atom('X')],
    )
    count_fn = model.AggregateFunction(symbol='#count', elements=[elem])
    return constraint(
        not_(
            model.
            AggregateRelation(aggregate=count_fn, right_op="=", right=level)
        )
    )


def check_solved_rules():
    def solved_atom(terms):
        name = aux_name(SOLVED)
        return atom(name, terms)

    def not_solved_atom(terms):
        name = aux_name(SOLVED, prefix=SNEG_PREFIX)
        return atom(name, terms)

    yield rule(
        not_solved_atom('Z'), [
            in_atom('X'),
            not_(solved_atom(['Z', 'X'])),
            solved_atom(['Z', '_']),
        ]
    )
    yield constraint([not_(not_solved_atom('Z')), solved_atom(['Z', '_'])])


def _guess_rules(modals, semantics):
    yield constraint([in_atom('X'), out_atom('X')])
    for modal in modals:
        if isinstance(modal, model.DefaultNegation):
            modal = modal.literal
        op = modal.op.lower()
        if semantics is KAHL_SEMANTICS:
            not_l = not_atom(modal.literal.symbol, modal.literal.arguments)
            m_condition = not_(not_l)
        else:
            m_condition = modal.literal
        condition = {
            'K': not_(modal.literal),
            'M': m_condition,
        }
        datom = modal_domain_atom(
            op, modal.literal.symbol, modal.literal.arguments
        )
        yield rule(
            disjunction([
                in_atom(modal_to_literal(modal)),
                out_atom(modal_to_literal(modal))
            ]), [datom]
        )
        yield rule(
            in_atom(modal_to_literal(modal)), [datom, condition[modal.op]]
        )
        yield rule(
            in_atom(modal_to_literal(modal)),
            [datom, out_atom(modal_to_literal(modal, switch_mode=True))]
        )


def _check_rules(modals):
    constraints = {
        'K': k_constraints,
        'M': m_constraints,
    }
    for modal in modals:
        if isinstance(modal, model.DefaultNegation):
            modal = modal.literal
        yield from constraints[modal.op](modal)


def domain_facts(modal_domains):
    for literal in modal_domains:
        op = literal.arguments[0].ast
        arg = literal.arguments[1]
        if isinstance(arg, model.ConstantTerm):
            symbol = arg.ast
            terms = []
        else:
            symbol = arg.symbol
            terms = arg.arguments
        yield fact(modal_domain_atom(op, symbol, terms))


def guess_rules(modals, modal_domains, semantics):
    yield from _guess_rules(modals, semantics)
    yield from domain_facts(modal_domains)


def check_rules(modals, path):
    yield fact(atom(aux_name(PATH_ATOM), '"{}"'.format(path)))
    yield from input_rules()
    yield from _check_rules(modals)


def guess_assignment_rules(modals, semantics):
    for modal in modals:
        literal = modal.literal
        modal_literal = modal_to_literal(modal)
        in_guess = in_atom(guess_term(modal))
        out_guess = out_atom(guess_term(modal))
        yield rule(modal_literal, in_guess)
        if modal.op == 'K':
            yield rule(modal_literal, [out_guess, not_(literal)])
        elif modal.op == 'M':
            if semantics is KAHL_SEMANTICS:
                not_l = not_atom(literal.symbol, literal.arguments)
                yield rule(modal_literal, [out_guess, not_(not_l)])
                yield rule(not_l, [out_guess, not_(literal)])
            else:
                yield rule(modal_literal, [out_guess, literal])
        else:
            assert False
