# -*- coding: utf-8 -*-

from ehex.parser import model
from ehex.filter import (Variables, Terms)
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
    ENVELOPE,
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


def envelope_atom(literal):
    function = functional_term(literal.symbol, literal.arguments)
    symbol = aux_name(ENVELOPE)
    return atom(symbol, function)


def program(statements=None):
    return model.Program(statements=statements or [])


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
    return model.Disjunction(literals=literals)


def conjunction(literals):
    return model.Conjunction(literals=literals)


def not_(literal):
    return model.DefaultNegation(literal=literal)


def modal_to_literal(modal):
    if modal.op == 'K':
        return not_k_literal(modal.literal)
    elif modal.op == 'M':
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
    terms = modal.literal.arguments
    domain_atoms = [domain_atom(term) for term in Variables(modal)]
    yield constraint(
        domain_atoms + [
            in_atom(term),
            path_atom(),
            cautious_inspection(symbol, terms),
        ]
    )
    yield constraint(
        domain_atoms + [
            out_atom(term),
            path_atom(),
            not_(cautious_inspection(symbol, terms)),
        ]
    )


def m_constraints(modal):
    term = guess_term(modal)
    symbol = modal.literal.symbol
    terms = [term for term in Terms(modal)]
    if any(Variables(modal.literal)):
        domain_atoms = [
            atom(
                aux_name(modal.literal.symbol, DOMAIN), modal.literal.arguments
            )
        ]
    else:
        domain_atoms = []
    variables = [
        aux_variable('x{}'.format(i)) for i, term in enumerate(terms)
        if not isinstance(term, model.VariableTerm)
    ]
    assignments = [
        model.BinaryRelation(op="=", left=x, right=terms[i])
        for i, x in enumerate(variables)
    ]
    var_iter = iter(variables)
    terms = [
        next(var_iter) if not isinstance(term, model.VariableTerm) else term
        for term in terms
    ]
    yield constraint(
        domain_atoms + [
            in_atom(term),
            path_atom(),
            not_(brave_inspection(symbol, terms)),
        ] + assignments
    )
    yield constraint(
        domain_atoms + [
            out_atom(term),
            path_atom(),
            brave_inspection(symbol, terms),
        ] + assignments
    )


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
    rules = ((atom(input_name, [in_name, 1, 'X']), in_atom('X')),
             (atom(input_name, [out_name, 1, 'X']), out_atom('X')), )
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
        name = aux_name('SOLVED')
        return atom(name, terms)

    def not_solved_atom(terms):
        name = aux_name('NOT_SOLVED')
        return atom(name, terms)

    yield rule(
        not_solved_atom('Z'), [
            in_atom('X'),
            not_(solved_atom(['Z', 'X'])),
            solved_atom(['Z', '_']),
        ]
    )
    yield constraint([not_(not_solved_atom('Z')), solved_atom(['Z', '_'])])


def guess_rules(modals):

    for modal in modals:
        if not any(Variables(modal)):
            yield fact(
                disjunction([
                    in_atom(modal_to_literal(modal)),
                    out_atom(modal_to_literal(modal))
                ])
            )
            continue

        domain_vars = ['X{}'.format(i) for i, _ in enumerate(Terms(modal))]
        yield rule(
            atom(aux_name(modal.literal.symbol, DOMAIN), domain_vars),
            envelope_atom(atom(modal.literal.symbol, domain_vars)),
        )
        yield rule(
            disjunction([
                in_atom(modal_to_literal(modal)),
                out_atom(modal_to_literal(modal))
            ]),
            envelope_atom(modal.literal)  # XXX: why XXX?
        )
        if modal.op == 'K':
            guessing_rules = (
                (in_atom(modal_to_literal(modal)), (
                    domain_atom(modal.literal.arguments),
                    not_(envelope_atom(modal.literal)),
                )),
            )  # yapf: disable
            yield from (rule(head, body) for head, body in guessing_rules)
        elif modal.op == 'M':
            pass
            # TODO: review, we don't need this rule, right?
            # yield rule(
            #     out_atom(modal_to_literal(modal)), [
            #         domain_atom(modal.literal.arguments),
            #         not_(envelope_atom(modal.literal))
            #     ]
            # )


def check_rules(modals):
    constraints = {'K': k_constraints, 'M': m_constraints}
    for modal in modals:
        yield from constraints[modal.op](modal)


def envelope_rules(envelope, domain):
    for literal in envelope:
        if isinstance(literal, model.StrongNegation):
            literal = sn_atom(
                literal.atom.symbol,
                literal.atom.arguments,
            )
        function = functional_term(
            literal.symbol,
            literal.arguments,
        )
        name = aux_name(ENVELOPE)
        yield fact(atom(name, function))
    for term in domain:
        name = aux_name(DOMAIN)
        yield fact(atom(name, term))


def guess_and_check_rules(modals, envelope, domain):
    yield from input_rules()
    yield from guess_rules(modals)
    yield from check_rules(modals)
    yield from envelope_rules(envelope, domain)


def guess_assignment_rules(modals):
    for modal in modals:
        literal = modal.literal
        modal_literal = modal_to_literal(modal)
        in_guess = in_atom(guess_term(modal))
        out_guess = out_atom(guess_term(modal))
        yield rule(modal_literal, in_guess)
        if modal.op == 'K':
            yield rule(modal_literal, [out_guess, not_(literal)])
        elif modal.op == 'M':
            not_l = not_atom(literal.symbol, literal.arguments)
            yield rule(modal_literal, [out_guess, not_(not_l)])
            yield rule(not_l, [out_guess, not_(literal)])
        else:
            assert False
