from ehex.codegen import grgen, ppgen
from ehex.codegen import rules as generate
from ehex.codegen.auxgen import ELPAuxGenerator
from ehex.codegen.elpgen import ELPGenerator
from ehex.solver.config import cfg
from ehex.utils import model
from ehex.utils.decorators import cached

_elpgen = ELPGenerator()
_auxgen = ELPAuxGenerator()


@cached
def elprender(obj):
    return _elpgen.render(obj)


@cached
def auxrender(obj):
    return _auxgen.render(obj)


def aux_program(elements):
    with _auxgen:
        elements = [
            e if isinstance(e, str) else auxrender(e) for e in elements
        ]
        if _auxgen.negations:
            elements += [
                auxrender(e)
                for e in generate.negation_constraints(_auxgen.negations)
            ]
    return "\n\n".join(elements)


def positive_program(elp):
    with _auxgen:
        elements = [auxrender(e) for e in ppgen.positive_program(elp)]
    return "\n\n".join(elements)


def generic_reduct(
    elp, guess_true_facts=None, guess_false_facts=None, guessing_hints=False
):
    elements = [
        "% Generic Epistemic Reduct",
        *grgen.generic_reduct(elp, guessing_hints=guessing_hints),
    ]
    if guess_true_facts:
        elements += [
            "% Replacement Rules for True Modals",
            *grgen.optimized_replacement_rules(guess_true_facts),
        ]
    if guess_false_facts:
        elements += [
            "% Replacement Rules for False Modals",
            *grgen.optimized_replacement_rules(guess_false_facts),
        ]
    return aux_program(elements)


def guessing_program(
    ground_facts, guess_true_facts=None, guessing_hints=False
):
    elements = []
    if ground_facts:
        elements += [
            "% Guessing Rules",
            *generate.guessing_rules(
                ground_facts, guessing_hints=guessing_hints
            ),
            "% Ground Facts",
            *generate.fact_rules(ground_facts),
        ]
    if guess_true_facts:
        elements += [
            "% Guessing Facts",
            *generate.fact_rules(guess_true_facts),
        ]
    return aux_program(elements)


def checking_program(ground_facts, reduct_out):
    elements = [
        "% Consistency Checking Program",
        *generate.input_rules(),
        *generate.checking_rules(ground_facts, reduct_out),
    ]
    return aux_program(elements)


def level_check(context):
    elements = [
        "% Cardinality Checking Program",
        aux_program(generate.cardinality_check(context.guess_size)),
    ]
    if context.omega:
        elements += [
            "% Subset Checking Program",
            *generate.member_rules(context.omega),
            *generate.subset_check(),
        ]
    return aux_program(elements)


def clingo_show_directives(ground_facts):
    atoms = [gnd.args[0].literal.atom for gnd in ground_facts]
    predicates = [
        (model.neg_name(a.name) if a.negation else a.name, len(a.args))
        for a in atoms
    ]
    directives = [f"#show {name}/{arity}." for name, arity in set(predicates)]
    return "\n".join(directives)


def enum_program(elp, facts, context=None):
    elements = [
        "%% Enum Program",
        clingo_show_directives(facts.ground),
        guessing_program(facts.ground, guessing_hints=False),
        generic_reduct(
            elp, facts.guess_true, facts.guess_false, guessing_hints=False
        ),
    ]
    if context:
        elements.append(level_check(context))
    return aux_program(elements)


def grounding_program(elp, facts):
    elements = [
        "% Grounding Program",
        guessing_program(facts.ground, guessing_hints=cfg.guessing_hints),
        generic_reduct(
            elp,
            facts.guess_true,
            facts.guess_false,
            guessing_hints=cfg.guessing_hints,
        ),
    ]
    return aux_program(elements)


def level_program(
    elp,
    facts,
    context,
    reduct_out,
    guess_true_facts=None,
):
    elements = [
        f"%% Level {context.level} Program",
        generic_reduct(
            elp,
            facts.guess_true,
            facts.guess_false,
            guessing_hints=cfg.guessing_hints,
        ),
    ]
    if facts.ground or guess_true_facts:
        elements.append(
            guessing_program(
                facts.ground,
                guess_true_facts=guess_true_facts,
                guessing_hints=cfg.guessing_hints,
            ),
        )
    if facts.ground:
        elements.append(checking_program(facts.ground, reduct_out))

    elements.append(level_check(context))
    return aux_program(elements)


def answer_set(elements):
    elements = [elprender(e) for e in elements]
    elements.sort()
    return f"{{{', '.join(elements)}}}"
