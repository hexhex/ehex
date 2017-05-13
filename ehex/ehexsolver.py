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
    Modals,
    ExtendedModals,
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


def get_envelope(program, options):
    oa_walker = OverApproximationWalker().walk
    envelope_src = render(oa_walker(program))
    if options.debug:
        with options.envelope_out.open('w') as envelope_file:
            envelope_file.write(envelope_src)
        print('Computing positive envelope and terms:')
        results = dlvhex(str(options.envelope_out))
    else:
        results = dlvhex(text=envelope_src)
    parse = answerset.parse
    envelope = set(next(parse(results)))
    modal_domains = {
        literal
        for literal in envelope
        if getattr(literal, 'symbol', '').startswith('aux__DOM')
    }
    envelope -= modal_domains
    if options.debug:
        as_render = answerset.render_answer_set
        print('Envelope:', as_render(envelope))
        print('Modal domains:', as_render(modal_domains))
    return envelope, modal_domains


def get_filter_predicates(envelope, modals):
    predicates = {  # TODO: refactoring, use filter from command line
        inject.aux_name(literal.atom.symbol, ehex.SNEG_PREFIX)
        if isinstance(literal, StrongNegation)
        else literal.symbol
        for literal in envelope
    } | {inject.aux_name(ehex.IN_ATOM)}
    if not predicates:
        predicates = {'none'}
    return predicates


def partition_literals(literals):
    answer_set = frozenset(literals)
    epistemic_guess = frozenset(
        literal for literal in answer_set
        if getattr(literal, 'symbol', '').startswith('aux__IN')
    )
    answer_set -= epistemic_guess
    return epistemic_guess, answer_set


def program_rules(program, modals):
    t_program = TranslationWalker().walk(program)
    yield from t_program.statements
    yield from inject.guess_assignment_rules(modals)


def solve(options):
    program = parse_program(options.src)
    envelope, modal_domains = get_envelope(program, options)
    emodals = ExtendedModals(program)
    modals = Modals(program)
    max_level = options.max_level or len(envelope)
    max_level = min(len(envelope), max_level)
    pfilter = get_filter_predicates(envelope, modals)
    gc_program = inject.program(
        inject.guess_and_check_rules(emodals, modal_domains)
    )
    program_src = (render(inject.program(program_rules(program, modals))))
    with options.program_out.open('w') as program_file:
        # This file is mandatory for HEX inspection
        program_file.write(program_src)
    path_atom = inject.fact(
        inject.atom(
            inject.aux_name('PATH'),
            '"{}"'.format(options.program_out),
        )
    )
    guess_src = (render(path_atom) + '\n\n' + render(gc_program))
    if options.debug:
        with options.guess_out.open('w') as guess_file:
            guess_file.write(guess_src)

    parse = answerset.parse
    as_render = answerset.render_answer_set

    solved_src = ''
    level = 0

    while level <= max_level:
        world_views = {}
        level_src = render(inject.level_constraint(level)) + '\n'
        if level > 0 and solved_src:
            level_src += '\n' + solved_src + '\n'
            for rule in inject.check_solved_rules():
                level_src += render(rule) + '\n'
        level_path = options.level_out.with_suffix('.{}.hex'.format(level))
        if options.debug:
            with level_path.open('w') as level_file:
                level_file.write(level_src)
        src = '\n'.join([
            level_src,
            guess_src,
            program_src,
        ])
        if options.debug:
            print('Results at level {}:'.format(level))
            results = dlvhex(
                str(level_path),
                str(options.guess_out),
                str(options.program_out),
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
                if not options.debug:
                    print(
                        'World view 1@{} wrt {}:'.
                        format(level, as_render(guess))
                    )
            if guess == first_wv and not options.debug:
                print(as_render(ans))

        if not options.debug:
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
                term = literal.arguments[0]
                symbol = inject.aux_name('SOLVED')
                solved_src += render(
                    inject.fact(inject.atom(symbol, (i, term)))
                ) + '\n'

        if options.debug:
            if world_views:
                print(
                    'Found {} world view(s) at level {}.'.
                    format(len(world_views), level)
                )
            else:
                print('No world view at level {}.'.format(level))
        if level == 0 and world_views:
            if max_level > 0 and options.debug:
                print(
                    'Solved at level 0, skipping {}.'.format(
                        'level 1'
                        if max_level == 1 else 'levels 1-{}'.format(max_level)
                    )
                )
            break
        level += 1
