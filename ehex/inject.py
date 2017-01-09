# -*- coding: utf-8 -*-

from ehex.parser import model
from ehex.filter import (
    Variables,
    Terms
)
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
    EPISTEMIC_NEGATION
)


def aux_name(symbol, prefix=''):
    prefix += '_' if prefix else ''
    return '{}{}{}'.format(
        AUX_MARKER, prefix.upper(), symbol.lstrip(AUX_MARKER))


def atom(symbol, terms=None):
    return model.Atom(symbol=symbol, arguments=terms)


def sn_atom(symbol, terms=None):
    return atom(
        aux_name(symbol, SNEG_PREFIX),
        terms
    )


def not_atom(symbol, terms=None):
    return atom(
        aux_name(symbol, DNEG_PREFIX),
        terms
    )


def not_k_atom(symbol, terms=None):
    return atom(
        aux_name(symbol, K_PREFIX),
        terms
    )


def m_atom(symbol, terms=None):
    return atom(
        aux_name(symbol, M_PREFIX),
        terms
    )


def program(statements=None):
    return model.Program(statements=statements or [])


def eneg_atom(terms):
    symbol = aux_name(EPISTEMIC_NEGATION)
    return atom(symbol, terms)


def envelope_atom(literal):
    function = functional_term(
        literal.symbol,
        literal.arguments
    )
    symbol = aux_name('ENVELOPE')  # TODO: use symbol
    return atom(symbol, function)


def domain_atom(term):
    symbol = aux_name('DOMAIN')
    return atom(symbol, term)


def in_atom(terms):
    symbol = aux_name(IN_ATOM)
    return atom(symbol, terms)


def out_atom(terms):
    symbol = aux_name(OUT_ATOM)
    return atom(symbol, terms)


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
        '&hexCautious[file, {}, {}, {}]'.format(path_variable, input_name, symbol),
        terms
    )


def brave_inspection(symbol, terms):
    input_name = aux_name(INPUT_ATOM)
    path_variable = aux_variable('path').ast
    return atom(
        '&hexBrave[file, {}, {}, {}]'.format(path_variable, input_name, symbol),
        terms,
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
        atom_ = sn_atom(
            literal.atom.symbol,
            literal.atom.arguments
        )
    else:
        atom_ = literal
    return not_k_atom(atom_.symbol, atom_.arguments)


def m_literal(literal):
    if isinstance(literal, model.StrongNegation):
        atom_ = sn_atom(
            literal.atom.symbol,
            literal.atom.arguments
        )
    else:
        atom_ = literal
    return m_atom(atom_.symbol, atom_.arguments)


path_atom = atom(aux_name(PATH_ATOM), aux_variable('path'))


def k_constraints(modal):
    term = guess_term(modal)
    symbol = modal.literal.symbol
    terms = modal.literal.arguments
    domain_atoms = [
        domain_atom(term) for term in Variables(modal)
    ]
    return [
        constraint(domain_atoms + [
            in_atom(term),
            path_atom,
            cautious_inspection(symbol, terms)
        ]),
        constraint(domain_atoms + [
            out_atom(term),
            path_atom,
            not_(cautious_inspection(symbol, terms))
        ]),
    ]


def m_constraints(modal):
    term = guess_term(modal)
    symbol = modal.literal.symbol
    terms = [term for term in Terms(modal)]
    if any(Variables(modal.literal)):
        domain_atoms = [
            atom(aux_name(modal.literal.symbol, 'DOMAIN'), modal.literal.arguments)
        ]
    else:
        domain_atoms = []
    variables = [
        aux_variable('x{}'.format(i))
        for i, term in enumerate(terms)
        if not isinstance(term, model.VariableTerm)
    ]
    assignments = [
        model.BinaryRelation(op="=", left=x, right=terms[i])
        for i, x in enumerate(variables)
    ]
    var_iter = iter(variables)
    terms = [
        next(var_iter) if not isinstance(term, model.VariableTerm)
        else term for term in terms
    ]
    return [
        constraint(domain_atoms + [
            in_atom(term),
            path_atom,
            not_(brave_inspection(symbol, terms))
        ] + assignments),
        constraint(domain_atoms + [
            out_atom(term),
            path_atom,
            brave_inspection(symbol, terms)
        ] + assignments),
    ]


def functional_term(symbol, terms=None):
    return model.FunctionalTerm(
        symbol=symbol,
        arguments=terms
    )

def guess_term(modal):
    literal = modal_to_literal(modal)
    arguments = getattr(literal, 'arguments', None)
    return functional_term(literal.symbol, arguments)



def input_rules():
    input_name = aux_name(INPUT_ATOM)
    in_name = aux_name(IN_ATOM)
    out_name = aux_name(OUT_ATOM)
    return [
        rule(atom(input_name, [in_name, 1, 'X']), in_atom('X')),
        rule(atom(input_name, [out_name, 1, 'X']), out_atom('X'))
    ]


def level_constraint(level):
    elem = model.AggregateElement(
        terms='X',
        literals=[out_atom('X')],
    )
    count_fn = model.AggregateFunction(
        symbol='#count',
        elements=[elem]
    )
    return constraint(not_(model.AggregateRelation(
        aggregate=count_fn,
        right_op="=",
        right=level
    )))


def check_solved_rules():
    def solved_atom(terms):
        name = aux_name('SOLVED')
        return atom(name, terms)
    def not_solved_atom(terms):
        name = aux_name('NOT_SOLVED')
        return atom(name, terms)
    return [
        rule(
            not_solved_atom('Z'), [
                in_atom('X'),
                not_(solved_atom(['Z', 'X'])),
                solved_atom(['Z', '_']),
            ]
        ),
        constraint([
            not_(not_solved_atom('Z')),
            solved_atom(['Z', '_'])
        ])
    ]



def guess_and_check(modals):

    prog = program()
    prog.statements.extend(input_rules())

    for modal in modals:
        if not any(Variables(modal)):
            guessing = fact(
                disjunction([
                    in_atom(modal_to_literal(modal)),
                    out_atom(modal_to_literal(modal))
                ])
            )
            prog.statements.append(guessing)
            continue

        domain_vars = ['X{}'.format(i) for i, in enumerate(Terms(modal))]
        domain_rule = rule(
            atom(aux_name(modal.literal.symbol, 'DOMAIN'), domain_vars),
            envelope_atom(atom(modal.literal.symbol, domain_vars))
        )
        prog.statements.append(domain_rule)
        guessing = rule(
            disjunction([
                in_atom(modal_to_literal(modal)),
                out_atom(modal_to_literal(modal))
            ]),
            envelope_atom(modal.literal) #XXX: why XXX?
        )
        prog.statements.append(guessing)
        if modal.op == 'K':
            # TODO: review, we could also use an in-guess, but that would
            # induce a &hexCautious check.
            input_name = aux_name(INPUT_ATOM)
            in_name = aux_name(IN_ATOM)
            guessing = [
                rule(
                    modal_to_literal(modal), [
                        domain_atom(modal.literal.arguments),
                        not_(envelope_atom(modal.literal))
                    ],
                ),
                rule(
                    atom(input_name, [in_name, 1, 'Z']), [
                        modal_to_literal(modal),
                        model.BinaryRelation(op="=", left='Z', right=guess_term(modal))
                    ]
                )
            ]
            prog.statements.extend(guessing)
        elif modal.op == 'M':
            pass
            # TODO: review, we don't need this rule, right?
            # guessing = rule(
            #     out_atom(modal_to_literal(modal)), [
            #         domain_atom(modal.literal.arguments),
            #         not_(envelope_atom(modal.literal))
            #     ]
            # )
            # prog.statements.append(guessing)

    constraints = {
        'K': k_constraints,
        'M': m_constraints
    }

    for modal in modals:
        prog.statements.extend(
            constraints[modal.op](modal)
        )

    return prog


def guess_assignments(modals):
    prog = program()
    for modal in modals:
        literal = modal.literal
        modal_literal = modal_to_literal(modal)
        in_guess = in_atom(guess_term(modal))
        out_guess = out_atom(guess_term(modal))
        rules = [
            rule(modal_literal, in_guess)
        ]
        if modal.op == 'K':
            rules.append(
                rule(
                    modal_literal,
                    [out_guess, not_(literal)]
                )
            )
        elif modal.op == 'M':
            not_l = not_atom(literal.symbol, literal.arguments)
            rules.extend([
                rule(
                    modal_literal,
                    [out_guess, not_(not_l)]
                ),
                rule(
                    not_l,
                    [out_guess, not_(literal)]
                )
            ])
        else:
            assert False

        prog.statements.extend(rules)

    return prog
