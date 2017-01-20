from pathlib import Path
from ehex.hexsolver import solve as dlvhex
from ehex.codegen import EHEXCodeGenerator

import ehex
from ehex import inject
from ehex.parser.model import (
    EHEXModelBuilderSemantics as Semantics,
    Atom,
    StrongNegation,
    KModal,
    MModal,
)
from ehex.parser.ehex import EHEXParser as Parser
from ehex.translation import (
    RewriteStrongNegationWalker,
    TranslationWalker,
    OverApproximationWalker,
)
from ehex.filter import (
    Variables,
    Modals,
    Terms,
)
import ehex.answerset as answerset

render = EHEXCodeGenerator().render


def parse_program(program_path):
    parser = Parser(parseinfo=False)
    with open(str(program_path)) as program_file:
        text = program_file.read()
    parsed = parser.parse(
        text, 'program', filename=str(program_path), semantics=Semantics()
    )
    return RewriteStrongNegationWalker().walk(parsed)


def get_envelope(program, envelope_path=None, debug=False):
    oa_walker = OverApproximationWalker().walk
    envelope_src = render(oa_walker(program))
    if debug:
        assert envelope_path is not None
        with open(str(envelope_path), 'w') as envelope_file:
            envelope_file.write(envelope_src)
        print('Computing positive envelope and terms:')
        results = dlvhex(str(envelope_path))
    else:
        results = dlvhex(text=envelope_src)
    parse = answerset.parse
    envelope = list(next(parse(results)))
    terms = set(render(term) for term in Terms(envelope))
    if debug:
        as_render = answerset.render_answer_set
        print('Envelope:', as_render(envelope))
        print('Terms:', as_render(terms))
    return envelope, terms


def compute_max_level(modals, domain, max_level=None, debug=False):
    cmax_level = sum(  # TODO: not optimal
        len(domain)**sum(1 for var in Variables(m))
        for m in modals
    )
    if debug:
        print('Computed maximum level is {}.'.format(cmax_level))
    if max_level is None:
        max_level = cmax_level
    else:
        max_level = min(max_level, cmax_level)
    return max_level


def get_filter_predicates(envelope, modals):
    predicates = {  # TODO: refactoring, use filter from command line
        inject.aux_name(literal.atom.symbol, ehex.SNEG_PREFIX)
        if isinstance(literal, StrongNegation)
        else literal.symbol
        for literal in envelope
    } | {
        inject.aux_name(
            modal.literal.symbol,
            {
                KModal: ehex.K_PREFIX,
                MModal: ehex.M_PREFIX
            }[type(modal)]
        )
        for modal in modals
    }
    if not predicates:
        predicates = {'none'}
    return predicates


def partition_literals(literals):
    literal_types = (Atom, StrongNegation)
    epistemic_guess = frozenset(literals)
    answer_set = set(
        literal for literal in epistemic_guess
        if isinstance(literal, literal_types)
    )
    epistemic_guess -= answer_set
    return epistemic_guess, answer_set


def program_rules(program, modals):
    t_program = TranslationWalker().walk(program)
    yield from t_program.statements
    yield from inject.guess_assignment_rules(modals)


def solve(file_name, debug=False, max_level=None):
    p = Path(file_name)
    program_path = Path(p.parent, p.stem + '.hex')
    guess_path = Path(p.parent, p.stem + '.guess.hex')
    envelope_path = Path(p.parent, p.stem + '.envelope.hex')

    program = parse_program(p)
    envelope, domain = get_envelope(program, envelope_path, debug=debug)
    modals = Modals(program)
    max_level = compute_max_level(
        modals, domain, max_level=max_level, debug=debug
    )

    modal_predicates = {
        (modal.literal.symbol, len(modal.literal.arguments or ()))
        for modal in modals
    }
    pfilter = get_filter_predicates(envelope, modals)

    envelope = [  # TODO: review, seems not optimal
        literal for literal in envelope
        if isinstance(literal, Atom)
        and len(literal.arguments or ()) > 0
        and (literal.symbol, len(literal.arguments or ()))
        in modal_predicates
    ] + [
        literal for literal in envelope
        if isinstance(literal, StrongNegation)  # TODO: transform envelope?
        and len(literal.atom.arguments or ()) > 0
        and (inject.aux_name(literal.atom.symbol, ehex.SNEG_PREFIX),
             len(literal.atom.arguments or []))
        in modal_predicates
    ]

    gc_program = inject.program(
        inject.guess_and_check_rules(modals, envelope, domain)
    )
    program_src = (render(inject.program(program_rules(program, modals))))
    with open(str(program_path), 'w') as program_file:
        # This file is mandatory for HEX inspection
        program_file.write(program_src)
    path_atom = inject.fact(
        inject.atom(inject.aux_name('PATH'), '"{}"'.format(program_path))
    )
    guess_src = (render(path_atom) + '\n\n' + render(gc_program))
    if debug:
        with open(str(guess_path), 'w') as guess_file:
            guess_file.write(guess_src)

    parse = answerset.parse
    as_render = answerset.render_answer_set

    solved_src = ''
    level = 0

    while level <= max_level:
        world_views = {}
        input_src = render(inject.level_constraint(level)) + '\n'
        if level > 0 and solved_src:
            input_src += '\n' + solved_src + '\n'
            for rule in inject.check_solved_rules():
                input_src += render(rule) + '\n'
        input_path = Path(p.parent, p.stem + '.level{}.hex'.format(level))
        if debug:
            with open(str(input_path), 'w') as input_file:
                input_file.write(input_src)
        src = '\n'.join([
            input_src,
            guess_src,
            program_src,
        ])
        if debug:
            print('Results at level {}:'.format(level))
            results = dlvhex(
                str(input_path),
                str(guess_path),
                str(program_path),
                pfilter=pfilter,
            )
        else:
            results = dlvhex(
                text=src,
                pfilter=pfilter,
            )

        first_wv = None
        for ans in parse(results):
            guess, ans = partition_literals(ans)
            wv = world_views.get(guess)
            if wv is None:
                wv = [ans]
                world_views[guess] = wv
            else:
                wv.append(ans)
            if first_wv is None:
                first_wv = guess
                if not debug:
                    print(
                        'World view 1@{} wrt {}:'.
                        format(level, as_render(guess))
                    )
            if guess == first_wv and not debug:
                print(as_render(ans))

        if not debug:
            for i, wv in enumerate(
                wv for wv in world_views if wv is not first_wv
            ):
                print(
                    'World view {}@{} wrt {}:'.
                    format(i + 2, level, as_render(wv))
                )
                for ans in world_views[wv]:
                    print(as_render(ans))

        for i, wv in enumerate(world_views):
            for literal in list(wv):
                term = answerset.unparse_literal(literal)
                symbol = inject.aux_name('SOLVED')
                solved_src += render(
                    inject.fact(inject.atom(symbol, (i, term)))
                ) + '\n'

        if debug:
            if world_views:
                print(
                    'Found {} world view(s) at level {}.'.
                    format(len(world_views), level)
                )
            else:
                print('No world view at level {}.'.format(level))
        if level == 0 and world_views:
            if max_level > 0 and debug:
                print(
                    'Solved at level 0, skipping {}.'.format(
                        'level 1'
                        if max_level == 1 else 'levels 1-{}'.format(max_level)
                    )
                )
            break
        level += 1
