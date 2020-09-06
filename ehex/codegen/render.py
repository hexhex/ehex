from ehex.codegen import rules as generate
from ehex.codegen.auxgen import ELPAuxGenerator
from ehex.codegen.elpgen import ELPGenerator
from ehex.codegen.grgen import GenericReductGenerator
from ehex.utils import model
from ehex.utils.decorators import cached

auxrender = ELPAuxGenerator().render
elprender = ELPGenerator().render


@cached
def _generic_reduct(elp):
    return GenericReductGenerator().render(elp)


@cached
def aux_rule(rule):
    return auxrender(rule)


def aux_program(elements):
    return "\n\n".join(
        [e if isinstance(e, str) else aux_rule(e) for e in elements]
    )


def generic_reduct(elp, guess_true_facts=None, guess_false_facts=None):
    elements = ["% Generic Epistemic Reduct", _generic_reduct(elp)]
    if guess_true_facts:
        elements += [
            "% Replacement Rules for True Modals",
            *generate.optimized_replacement_rules(guess_true_facts),
        ]
    if guess_false_facts:
        elements += [
            "% Replacement Rules for False Modals",
            *generate.optimized_replacement_rules(guess_false_facts),
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
        generic_reduct(elp, facts.guess_true, facts.guess_false),
    ]
    if context:
        elements.append(level_check(context))
    return aux_program(elements)


def grounding_program(elp, facts, guessing_hints=False):
    elements = [
        "% Grounding Program",
        guessing_program(facts.ground, guessing_hints=guessing_hints),
        generic_reduct(elp, facts.guess_true, facts.guess_false),
    ]
    return aux_program(elements)


def level_program(
    elp,
    facts,
    context,
    reduct_out,
    guess_true_facts=None,
    guessing_hints=False,
):
    elements = [
        f"%% Level {context.level} Program",
        generic_reduct(elp, facts.guess_true, facts.guess_false),
    ]
    if facts.ground or guess_true_facts:
        elements.append(
            guessing_program(
                facts.ground,
                guess_true_facts=guess_true_facts,
                guessing_hints=guessing_hints,
            ),
        )
    if facts.ground:
        elements.append(checking_program(facts.ground, reduct_out))

    elements.append(level_check(context))
    return aux_program(elements)


@cached
def ans_atom(atom):
    return elprender(atom)


def answer_set(elements):
    elements = [ans_atom(e) for e in elements]
    elements.sort()
    return f"{{{', '.join(elements)}}}"
