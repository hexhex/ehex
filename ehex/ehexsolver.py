import sys
from ehex.hexsolver import solve as dlvhex
from ehex.clingo import solve as clingo
from ehex.codegen import EHEXCodeGenerator

import ehex
from ehex import fragments
from ehex.parser.model import (
    EHEXModelBuilderSemantics as Semantics,
    StrongNegation,
    ConstantTerm,
    Modal,
    DefaultNegation,
)
from ehex.parser.ehex import EHEXParser as Parser
from ehex.translation import (
    RewriteStrongNegationWalker,
    TranslationWalker,
    OverApproximationWalker,
)
from ehex.filter import Modals

import ehex.answerset as answerset

render = EHEXCodeGenerator().render


class Context:

    def __init__(self, options):
        self.fragments = {}
        self.literals = {"consequences": {}}
        self.src = src = {}
        self.parse_input(options)
        self.create_modal_literals()
        self.compute_envelope(options)
        self.create_guess()
        self.create_check(options)
        self.create_reduct()
        self.create_filter_predicates()
        self.create_ground_modals()
        self.render_fragments(self.fragments)
        if options.planning_mode:
            self.append_src(
                'guess_rules',
                ':- aux__IN(aux__NOT_K_goal).',
                ':- aux__OUT(aux__M_goal).',
            )
        self.set_src('lp_program', src['reduct_program'], src['guess_rules'])
        self.set_src('gc_rules', src['guess_rules'], src['check_rules'])
        self.set_src('solved_constraints')
        self.create_show_k_src()
        self.create_show_m_src()
        self.min_level = 0
        max_level = len(self.literals['modal_domains'])
        if options.max_level is not None:
            max_level = min(max_level, options.max_level)
        self.max_level = max_level

    @staticmethod
    def _parse_program(program_path):
        parser = Parser(parseinfo=False)
        with open(str(program_path)) as program_file:
            text = program_file.read()
        parsed = parser.parse(
            text, 'program', filename=str(program_path), semantics=Semantics()
        )
        return RewriteStrongNegationWalker().walk(parsed)

    @staticmethod
    def _extract_modals(modal_domains, mode):
        for atom in modal_domains:
            op = atom.arguments[0].ast
            if op != mode:
                continue
            model = atom.arguments[1]
            if isinstance(model, ConstantTerm):
                model = fragments.atom(model.ast)
            yield model

    @staticmethod
    def undo_negation_symbol(item):
        return render(item).replace('¬', 'aux__NEG_')

    @staticmethod
    def create_show_directives(atoms):
        for atom in atoms:
            num = len(getattr(atom, 'arguments', []))
            yield '#show {}/{}.'.format(getattr(atom, 'symbol', atom.ast), num)

    def parse_input(self, options):
        self.fragments['ehex_program'] = self._parse_program(options.ehex_in)

    def create_modal_literals(self):
        self.literals.update({
            'modals': Modals(self.fragments['ehex_program'])
        })

    def create_guess(self):
        self.fragments['guess_rules'] = fragments.program(
            fragments.guess_rules(
                self.literals['modals'], self.literals['modal_domains']
            )
        )

    def create_check(self, options):
        self.fragments['check_rules'] = fragments.program(
            fragments.check_rules(self.literals['modals'], options.reduct_out)
        )

    def create_reduct(self):
        t_program = TranslationWalker().walk(self.fragments['ehex_program'])
        rules = list(t_program.statements)
        rules += list(
            fragments.guess_assignment_rules(self.literals['modals'])
        )
        self.fragments['reduct_program'] = fragments.program(rules)

    def render_fragments(self, fragments_map):
        for key, fragment in fragments_map.items():
            self.src[key] = render(fragment)

    def compute_envelope(self, options):
        oa_walker = OverApproximationWalker().walk
        envelope_src = render(oa_walker(self.fragments['ehex_program']))
        if options.debug:
            with options.envelope_out.open('w') as envelope_file:
                envelope_file.write(envelope_src)
            print('Computing positive envelope and terms:', file=sys.stderr)
            results = clingo(
                str(options.envelope_out), debug=True, print_errors=True
            )
        else:
            results = clingo(text=envelope_src)
        parse = answerset.parse
        envelope = set(next(parse(results)))
        modal_domains = {
            literal
            for literal in envelope
            if getattr(literal, 'symbol', '').startswith('aux__DOM')
        }
        envelope -= modal_domains
        if options.debug:
            print('Envelope:', answerset.render(envelope), file=sys.stderr)
            print(
                'Modal domains:',
                answerset.render(modal_domains), file=sys.stderr
            )
        self.literals.update({
            'envelope': envelope,
            'modal_domains': modal_domains
        })

    def create_filter_predicates(self):
        predicates = {  # TODO: use filter from command line
            fragments.aux_name(literal.atom.symbol, ehex.SNEG_PREFIX)
            if isinstance(literal, StrongNegation)
            else literal.symbol
            for literal in self.literals['envelope']
        } | {fragments.aux_name(ehex.IN_ATOM)}
        if not predicates:
            predicates = {'none'}
        self.literals['filter_predicates'] = predicates

    def create_ground_modals(self):
        modal_domains = self.literals['modal_domains']
        self.literals.update({
            'ground_k_atoms': {
                self.undo_negation_symbol(model): model
                for model in
                self._extract_modals(modal_domains, 'k')
            },
            'ground_m_atoms': {
                render(model): model
                for model in
                self._extract_modals(modal_domains, 'm')
            }
        })

    def compute_cautious_consequences(self, options, extra_src='', key=None):
        enum_mode = 'cautious'
        target = self.literals['consequences']
        if key is not None:
            target[key] = target.get(key, {})
            target = target[key]
        if not self.literals['ground_k_atoms']:
            target[enum_mode] = {}
            return
        src = self.src['show_k_program'] + extra_src
        result = clingo(
            debug=options.debug, print_errors=options.debug,
            text=src, enum_mode=enum_mode, project='show'
        )
        for ans in answerset.parse(result):
            target[enum_mode] = {
                self.undo_negation_symbol(item): item
                for item in ans
            }
            return
        target[enum_mode] = None

    def compute_brave_consequences(self, options, key=None, extra_src=''):
        enum_mode = 'brave'
        target = self.literals['consequences']
        if key is not None:
            target[key] = target.get(key, {})
            target = target[key]
        if not self.literals['ground_m_atoms']:
            target[enum_mode] = {}
            return
        src = self.src['show_m_program'] + extra_src
        result = clingo(
            debug=options.debug, print_errors=options.debug,
            text=src, enum_mode=enum_mode, project='show'
        )
        for ans in answerset.parse(result):
            target[enum_mode] = {
                self.undo_negation_symbol(item): item
                for item in ans
            }
            return
        target[enum_mode] = None

    def render_k_constraints(self, level):
        literals = self.literals['consequences'][level]['cautious'].values()
        rules = []
        for literal in literals:
            rules.append(
                fragments.
                fact(fragments.out_atom(fragments.not_k_literal(literal)))
            )
        self.src['k_constraints'] = render(fragments.program(rules))

    def render_m_constraints(self, level):
        keys = (
            self.literals['ground_m_atoms'].keys() -
            self.literals['consequences'][level]['brave'].keys()
        )
        literals = [
            self.literals['ground_m_atoms'][key]
            for key in keys
        ]
        rules = []
        for literal in literals:
            rules.append(
                fragments.constraint(
                    fragments.
                    not_(fragments.out_atom(fragments.m_literal(literal)))
                )
            )
        self.src['m_constraints'] = render(fragments.program(rules))

    def set_src(self, name, *src):
        sep = '\n\n%%% {} %%%\n\n'.format(name)
        self.src[name] = sep.join(src)

    def append_src(self, name, *src):
        self.set_src(name, self.src[name], *src)

    def create_show_k_src(self):
        ground_k_atoms = self.literals['ground_k_atoms']
        if not ground_k_atoms:
            self.set_src('show_k_program')
            return

        directives = self.create_show_directives(
            ground_k_atoms.values()
        )
        self.set_src(
            'show_k_program', *set(directives), self.src['lp_program']
        )

    def create_show_m_src(self):
        ground_m_atoms = self.literals['ground_m_atoms']
        if not ground_m_atoms:
            self.set_src('show_m_program')
            return

        directives = self.create_show_directives(
            ground_m_atoms.values()
        )
        self.set_src(
            'show_m_program', *set(directives), self.src['lp_program']
        )

    def render_solved_constraints(self, world_views, level):
        world_views = world_views[level]
        if not world_views:
            return
        symbol = fragments.aux_name(ehex.SOLVED)

        def rules():
            for i, wv in enumerate(world_views):
                for literal in wv:
                    term = fragments.modal_to_literal(literal)
                    name = '"w{}@{}"'.format(i + 1, level)
                    yield fragments.fact(fragments.atom(symbol, [name, term]))
            yield from fragments.check_solved_rules()

        self.append_src(
            'solved_constraints', render(fragments.program(rules()))
        )


class Solver:

    def __init__(self, context):
        self.context = context
        self.world_views = {}

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
            reduct_file.write(src['reduct_program'])
        if options.debug:
            with options.guess_out.open('w') as guess_file:
                guess_file.write(src['gc_rules'])

        context.compute_cautious_consequences(options)
        context.min_level += len(context.literals['consequences']['cautious'])
        context.compute_brave_consequences(options)
        context.min_level += len(context.literals['ground_m_atoms']) - len(
            context.literals['consequences']['brave']
        )

        for level in range(context.min_level, context.max_level + 1):
            context.set_src(level, render(fragments.level_constraint(level)))
            self.world_views[level] = {}
            if level > context.min_level:
                context.render_solved_constraints(self.world_views, level - 1)
                if src['solved_constraints']:
                    context.append_src(level, src['solved_constraints'])

            context.compute_cautious_consequences(
                options, extra_src=src[level], key=level
            )
            if context.literals['consequences'][level]['cautious'] is None:
                continue

            context.compute_brave_consequences(
                options, extra_src=src[level], key=level
            )
            if context.literals['consequences'][level]['brave'] is None:
                continue

            check_level = len(
                context.literals['consequences'][level]['cautious']
            )
            check_level += len(context.literals['ground_m_atoms']) - len(
                context.literals['consequences'][level]['brave']
            )
            if level < check_level:
                continue

            context.render_k_constraints(level)
            context.render_m_constraints(level)
            context.append_src(
                level, src['k_constraints'], src['m_constraints']
            )

            if options.debug:
                level_path = options.level_out.with_suffix(
                    '.{}.hex'.format(level)
                )
                with level_path.open('w') as level_file:
                    level_file.write(src[level])
                print('Results at level {}:'.format(level), file=sys.stderr)
                results = dlvhex(
                    str(level_path),
                    str(options.guess_out),
                    str(options.reduct_out),
                    debug=True,
                    print_errors=True,
                    pfilter=context.literals['filter_predicates'],
                )
            else:
                context.set_src(
                    'problem',
                    src[level],
                    src['reduct_program'],
                    src['gc_rules'],
                )
                results = dlvhex(
                    text=src['problem'],
                    pfilter=context.literals['filter_predicates'],
                )

            for ans in answerset.parse(results):
                guess, ans = self.segregate_literals(ans)
                if guess not in self.world_views[level]:
                    self.world_views[level][guess] = [ans]
                else:
                    self.world_views[level][guess].append(ans)
                if 'first' not in self.world_views:
                    self.world_views['first'] = guess
                    if not options.debug:
                        print(
                            'World view 1@{} wrt {}:'.
                            format(level, answerset.render(guess))
                        )
                if guess == self.world_views['first'] and not options.debug:
                    print(answerset.render(ans))

            if not options.debug:
                for i, wv in enumerate(self.world_views[level]):
                    if wv == self.world_views['first']:
                        continue
                    print(
                        'World view {}@{} wrt {}:'.
                        format(i + 1, level, answerset.render(wv))
                    )
                    for ans in self.world_views[level][wv]:
                        print(answerset.render(ans))

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
