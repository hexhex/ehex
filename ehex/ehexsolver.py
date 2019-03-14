import re
import sys
from ehex.hexsolver import solve as dlvhex
from ehex.clingo import solve as clingo
from ehex.codegen import EHEXCodeGenerator
from ehex.utils import flatten

import ehex
from ehex import fragments, answerset, aspif
from ehex.parser.model import (
    Atom,
    DefaultNegation,
    EHEXModelBuilderSemantics as Semantics,
    Modal,
    StrongNegation,
)
from ehex.parser.ehex import EHEXParser
from ehex.translation import (
    GroundingResultWalker,
    OverApproximationWalker,
    RewriteStrongNegationWalker,
    TranslationWalker,
)
from ehex.filter import ClassicalLiterals

_render = EHEXCodeGenerator().render


def render(fragment):
    return '\n\n'.join(_render(item) for item in flatten(fragment))


def nkey(obj):
    if not isinstance(obj, str):
        obj = render(obj)
    return (*answerset.generate_literals(answerset.nested_split(obj)),)[-2:]


class Context:

    ground_modals = None
    brave_modals = None
    cautious_modals = None
    filter_predicates = None

    def __init__(self, options):
        self.fragments = {}
        self.src = {}

        self.parse_input(options)
        reduct_modals = self.create_reduct(options)
        self.create_guessing(options, reduct_modals)
        self.create_checking(options, reduct_modals)

        envelope, envelope_modals = self.compute_envelope(options)
        self._set_ground_modals(envelope_modals)
        self.create_filter_predicates(envelope)

        facts = {
            'domain': {*self.ground_modals},
            'in': set(),
            'out': set(),
            'asp': set()
        }
        self.update_fragments(options, facts)

        if options.enable_queries:
            cautious = self.compute_consequences('cautious', options)
            brave = self.compute_consequences('brave', options)
            facts['out'] |= self.create_k_facts(cautious)
            facts['out'] |= self.create_m_facts(brave)
            facts['domain'] -= {*facts['out']}
            self.update_fragments(options, facts)

        if options.planning_mode:
            facts['in'] |= {nkey('M goal')}
            facts['out'] |= {nkey('not K goal')}
            horizon = [
                a.arguments[0].ast for a in envelope
                if isinstance(a, Atom) and a.symbol == 'horizon'
            ][0]
            self.update_fragments(options, facts)

        if options.grounder == 'asp':
            asp_modals, asp_facts = self.asp_grounding(options)
            facts['domain'] &= asp_modals
            facts['asp'] |= asp_facts
            # facts['in'] |= asp_facts
            self.update_fragments(options, facts)

        self.facts = facts
        self.set_src('world_views.fragment', '')
        self.max_level = len(self.ground_modals) - len(facts['in'] | facts['asp'])
        if options.enable_queries:
            self.min_level = len(facts['out'])
        else:
            self.min_level = 0
        if options.planning_mode:
            self.min_level = len(self.ground_modals) - (horizon + 1)
            self.max_level = self.min_level
        if options.max_level is not None:
            self.max_level = min(self.max_level, options.max_level)

    @staticmethod
    def _parse_program(program_path):
        parser = EHEXParser(parseinfo=False)
        with open(str(program_path)) as program_file:
            text = program_file.read()
        parsed = parser.parse(
            text, 'program', filename=str(program_path), semantics=Semantics()
        )
        return RewriteStrongNegationWalker().walk(parsed)

    def parse_input(self, options):
        self.fragments['ehex_program'] = self._parse_program(options.ehex_in)

    def create_reduct(self, options):
        walker = TranslationWalker(options.semantics)
        self.fragments['generic_reduct'] = walker.walk(
            self.fragments['ehex_program']
        )
        return walker.modals

    def create_guessing(self, options, reduct_modals):
        self.fragments['guessing_rules'] = fragments.guessing_rules(
            reduct_modals, options.optimize_guessing
        )
        if options.optimize_guessing:
            self.fragments['guessing_hints'] = fragments.guessing_hints(
                reduct_modals,
                semantics=options.semantics,
            )

    def compute_envelope(self, options):
        oa_walker = OverApproximationWalker().walk
        self.set_src(
            options.envelope_out.name,
            render(oa_walker(self.fragments['ehex_program']))
        )
        if options.debug:
            with options.envelope_out.open('w') as envelope_file:
                envelope_file.write(self.src[options.envelope_out.name])
            print('Computing positive envelope:', file=sys.stderr)
            results = clingo(
                str(options.envelope_out), debug=True, print_errors=True
            )
        else:
            results = clingo(src=self.src[options.envelope_out.name])
        envelope = set(
            GroundingResultWalker().walk(next(answerset.parse(results)))
        )
        ground_modals = {
            literal
            for literal in envelope if isinstance(literal, Modal)
        }
        envelope -= ground_modals

        if options.debug:
            print('Envelope:', answerset.render(envelope), file=sys.stderr)
            print(
                'Ground modals:', answerset.render(ground_modals),
                file=sys.stderr
            )
        return envelope, ground_modals

    def update_fragments(self, options, facts):
        self.create_guessing_domain(facts['domain'])
        self.create_guessing_facts(
            in_facts=facts['in'], out_facts=facts['out']
        )
        if facts['asp']:
            asp_facts = {
                fact: fragments.guessing_atom(self.ground_modals[fact])
                for fact in facts['asp']
            }
            self.fragments['asp_facts'] = [
                fragments.fact(asp_facts[fact])
                for fact in sorted(asp_facts)
            ]


        self.render_fragments(options)
        if options.enable_queries:
            self.create_show_cautious(self.cautious_modals)
            self.create_show_brave(self.brave_modals)

    def update_level(self, options, level, out_facts):
        self.create_guessing_facts(out_facts=out_facts, level=level)
        self.render_fragments(options, update_src=False)

    def create_guessing_domain(self, domain_modals):
        modals = [self.ground_modals[modal] for modal in sorted(domain_modals)]
        self.fragments['guessing_domain'] = fragments.domain_facts(modals)

    def create_guessing_facts(self, in_facts=(), out_facts=(), level=None):
        if not (in_facts or out_facts):
            return
        key = 'guessing_facts'
        if level is not None:
            key += '.{}'.format(level)
        in_facts = [
            fragments.in_atom(fragments.guessing_term(self.ground_modals[f]))
            for f in sorted(in_facts)
        ]
        out_facts = [
            fragments.out_atom(fragments.guessing_term(self.ground_modals[f]))
            for f in sorted(out_facts)
        ]
        self.fragments[key] = [fragments.fact(f) for f in in_facts + out_facts]

    def asp_grounding(self, options):
        out = options.ehex_in.with_suffix('.grounding.lp')
        self.set_src(
            out.name, self.src['intermediate.lp'],
            self.src.get('guessing_hints.fragment', ''),
        )
        if options.debug:
            out = options.ehex_in.with_suffix('.grounding.lp')
            with out.open('w') as grounding_file:
                grounding_file.write(self.src[out.name])
            print('Grounding the generic reduct:', file=sys.stderr)
            result = clingo(
                str(out), mode='gringo', output='intermediate', debug=True,
                print_errors=True
            )
        else:
            result = clingo(
                src=self.src[out.name], mode='gringo', output='intermediate'
            )
        MODAL = re.compile(
            '{}({}|{})_(?:({})_)?(.*)'.format(
                ehex.AUX_MARKER, ehex.K_PREFIX, ehex.M_PREFIX, ehex.SNEG_PREFIX
            )
        )
        get_symbol = {'NOT_K': 'K', 'NEG': '-'}.get

        def repl(s):
            match = MODAL.match(s)
            if not match:
                return None
            m, neg, lit = match.groups()
            m = get_symbol(m, m)
            neg = get_symbol(neg, '')
            return nkey('{} {}{}'.format(m, neg, lit))

        facts, modals = aspif.relevant(result, repl)
        return {*modals}, {*facts}

    def create_checking(self, options, reduct_modals):
        self.fragments['checking_rules'] = fragments.checking_rules(
            reduct_modals, options.reduct_out
        )

    def render_fragments(self, options, update_src=True):
        fragments_map = self.fragments
        for key in [*fragments_map]:
            fragment = fragments_map.pop(key)
            self.set_src('{}.fragment'.format(key), render(fragment))
        if not update_src:
            return
        self.set_src(
            'intermediate.lp',
            self.src['generic_reduct.fragment'],
            self.src.get('asp_facts.fragment', ''),
            self.src['guessing_rules.fragment'],
            self.src['guessing_domain.fragment'],
            self.src.get('guessing_facts.fragment', ''),
        )
        self.set_src(
            options.reduct_out.name,
            self.src['generic_reduct.fragment'],
            self.src.get('asp_facts.fragment', ''),
        )
        self.set_src(
            options.guessing_out.name,
            self.src['guessing_rules.fragment'],
            self.src['guessing_domain.fragment'],
            self.src.get('guessing_facts.fragment', ''),
            self.src['checking_rules.fragment'],
        )
        if options.optimize_guessing:
            self.append_src(
                options.guessing_out.name,
                self.src['guessing_hints.fragment']
            )

    @staticmethod
    def create_show_directives(modals):
        rewrite = RewriteStrongNegationWalker().walk
        directives = {
            '#show {}/{}.'.format(atom.symbol, len(atom.arguments or ()))
            for atom in rewrite(ClassicalLiterals(modals))
        }
        return sorted(directives)

    def create_filter_predicates(self, envelope):
        predicates = {  # TODO: use filter from command line
            fragments.aux_name(literal.atom.symbol, ehex.SNEG_PREFIX)
            if isinstance(literal, StrongNegation)
            else literal.symbol
            for literal in envelope
        } | {fragments.aux_name(ehex.IN_ATOM)}
        if not predicates:
            predicates = {'none'}
        self.filter_predicates = predicates

    def _set_ground_modals(self, modals):
        ground_modals = {}
        cautious_modals = {}
        brave_modals = {}
        for modal in modals:
            key = nkey(modal)
            ground_modals[key] = modal
            if modal.op == 'K':
                cautious_modals[key] = modal
            else:
                assert modal.op == 'M'
                brave_modals[key] = modal
        self.ground_modals = ground_modals
        self.cautious_modals = cautious_modals
        self.brave_modals = brave_modals

    def compute_consequences(self, enum_mode, options, extra_src='', key=None):
        if not getattr(self, '{}_modals'.format(enum_mode)):
            return {}
        src_key = '{}.lp'.format(enum_mode)
        src = self.src[src_key]
        if extra_src:
            src += '\n' + extra_src
        clingo_args = {
            'debug': options.debug,
            'print_errors': options.debug,
            'enum_mode': enum_mode,
            'project': 'show'
        }
        if options.debug:
            out = options.ehex_in.with_suffix('.{}'.format(src_key))
            if key is not None:
                out = out.with_suffix('.{}.lp'.format(key))
            with out.open('w') as out_file:
                out_file.write(src)
            result = clingo(str(out), **clingo_args)
        else:
            result = clingo(src=src, **clingo_args)
        for ans in answerset.parse(result):
            return [nkey(item) for item in ans]
        return None

    def create_k_facts(self, consequences):
        return {*self.cautious_modals} & {('K', *key) for key in consequences}

    def create_m_facts(self, consequences):
        return {*self.brave_modals} - {('M', *key) for key in consequences}

    def set_src(self, name, *src):
        self.src[name] = '%%% {} %%%\n'.format(name)
        self.append_src(name, *src)

    def append_src(self, name, *src):
        src = '\n\n'.join([s.strip() for s in src if s.strip()])
        if src:
            self.src[name] += '\n{}\n'.format(src)

    def create_show_cautious(self, cautious_modals):
        if not cautious_modals:
            self.set_src('cautious.lp', '% no K atoms')
            return
        directives = self.create_show_directives(cautious_modals.values())
        self.set_src(
            'cautious.lp', '\n'.join(directives),
            self.src['intermediate.lp']
        )

    def create_show_brave(self, brave_modals):
        if not brave_modals:
            self.set_src('brave.lp', '% no M atoms')
            return
        directives = self.create_show_directives(brave_modals.values())
        self.set_src(
            'brave.lp', '\n'.join(directives), self.src['intermediate.lp']
        )

    def render_subset_constraints(self, world_views, level):
        world_views = world_views[level]
        if not world_views:
            return
        symbol = fragments.aux_name(ehex.SOLVED)

        def rules():
            for i, wv in enumerate(world_views):
                for literal in wv:
                    term = fragments.guessing_term(literal)
                    name = '"w{}@{}"'.format(i + 1, level)
                    yield fragments.fact(fragments.atom(symbol, [name, term]))
            yield from fragments.check_subset_rules()

        self.append_src('world_views.fragment', render(rules()))


class Solver:

    def __init__(self, context):
        self.context = context
        self.world_views = {'count': 0}

    @staticmethod
    def segregate_literals(literals):
        answer_set = frozenset(literals)
        epistemic_guess = frozenset(
            literal for literal in answer_set
            if isinstance(literal, (DefaultNegation, Modal))
        )
        answer_set -= epistemic_guess
        return epistemic_guess, answer_set

    def solve(self, options):
        context = self.context
        src = context.src

        with options.reduct_out.open('w') as reduct_file:
            # This file is mandatory for HEX inspection
            reduct_file.write(src[options.reduct_out.name])
        if options.debug:
            with options.guessing_out.open('w') as guessing_file:
                guessing_file.write(src[options.guessing_out.name])

        worlds_out = options.ehex_in.with_suffix('.worlds')
        with worlds_out.open('w') as worlds_file:
            worlds_file.write('')

        def print_or_append(text):
            if options.debug:
                with worlds_out.open('a') as worlds_file:
                    worlds_file.write(text + '\n')
            else:
                print(text)

        for level in range(context.min_level, context.max_level + 1):
            level_out = options.level_out.with_suffix('.{}.lp'.format(level))
            context.set_src(
                level_out.name, render(fragments.level_constraint(level))
            )
            self.world_views[level] = {}
            if level > context.min_level:
                context.render_subset_constraints(self.world_views, level - 1)
                context.append_src(level_out.name, src['world_views.fragment'])

            if options.enable_queries:
                cautious = context.compute_consequences(
                    'cautious', options, extra_src=src[level_out.name],
                    key=level
                )
                if cautious is None:
                    continue

                brave = context.compute_consequences(
                    'brave', options, extra_src=src[level_out.name], key=level
                )
                if brave is None:
                    continue

                checking_level = (
                    len(cautious)
                    + len(context.brave_modals)
                    - len(brave)
                )
                if checking_level > level:
                    continue

                if checking_level > context.min_level:
                    out_facts = context.create_k_facts(cautious)
                    out_facts |= context.create_m_facts(brave)
                    out_facts -= context.facts['out']
                    context.update_level(options, level, out_facts)
                    context.append_src(
                        level_out.name,
                        context.src['guessing_facts.{}.fragment'.format(level)]
                    )

            if options.debug:
                with level_out.open('w') as level_file:
                    level_file.write(src[level_out.name])
                print('Results at level {}:'.format(level), file=sys.stderr)
                results = dlvhex(
                    str(level_out),
                    str(options.guessing_out),
                    str(options.reduct_out),
                    debug=True,
                    print_errors=True,
                    pfilter=context.filter_predicates,
                )
            else:
                context.set_src(
                    'problem',
                    src[level_out.name],
                    src[options.reduct_out.name],
                    src[options.guessing_out.name],
                )
                results = dlvhex(
                    src=src['problem'],
                    pfilter=context.filter_predicates,
                )

            wv_info = (
                'World view {}\n'
                'True ({}): {}\n'
                'False ({}): {}'
            )
            first_wv = None
            all_modals = {
                lit: modal
                if modal.op == 'M' else DefaultNegation(literal=modal)
                for lit, modal in context.ground_modals.items()
            }
            in_facts = {
                key: all_modals[key]
                for key in context.facts['in'] | context.facts['asp']
            }
            for ans in answerset.parse(results):
                guess, ans = self.segregate_literals(ans)
                self.world_views[level].setdefault(guess, []).append(ans)
                if first_wv is None:
                    first_wv = guess
                    in_guess = {nkey(lit): lit for lit in guess}
                    in_guess.update(in_facts)
                    out_guess = {
                        lit: modal
                        for lit, modal in all_modals.items()
                        if lit not in in_guess
                    }

                    self.world_views['count'] += 1
                    print_or_append(
                        wv_info.format(
                            self.world_views['count'], len(in_guess),
                            answerset.render(in_guess.values()),
                            len(out_guess),
                            answerset.render(out_guess.values())
                        )
                    )
                if guess == first_wv:
                    print_or_append(answerset.render(ans))

            other_wvs = (
                wv for wv in self.world_views[level] if wv is not first_wv
            )
            for wv in other_wvs:
                in_guess = {nkey(lit): lit for lit in guess}
                in_guess.update(in_facts)
                out_guess = {
                    lit: modal
                    for lit, modal in all_modals.items()
                    if lit not in in_guess
                }
                self.world_views['count'] += 1
                print_or_append(
                    wv_info.format(
                        self.world_views['count'], len(in_guess),
                        answerset.render(in_guess.values()), len(out_guess),
                        answerset.render(out_guess.values())
                    )
                )
                for ans in self.world_views[level][wv]:
                    print_or_append(answerset.render(ans))

            if options.debug:
                if self.world_views[level]:
                    print(
                        'Found {} world view(s) at level {}.'.format(
                            len(self.world_views[level]), level
                        ), file=sys.stderr
                    )
                else:
                    print(
                        'No world view at level {}.'.format(level),
                        file=sys.stderr
                    )
            if level == 0 and self.world_views[level]:
                if context.max_level > 0 and options.debug:
                    print(
                        'Solved at level 0, skipping {}.'.format(
                            'level 1' if context.max_level == 1 else
                            'levels 1-{}'.format(context.max_level)
                        )
                    )
                break
            if options.planning_mode and self.world_views[level]:
                break
