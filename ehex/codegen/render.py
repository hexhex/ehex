from ehex.codegen.ppgen import PositiveProgramGenerator
from ehex.codegen.elpgen import ELPGenerator
from ehex.codegen.asgen import AnswerSetGenerator
from ehex.codegen.grgen import GenericReductGenerator
from ehex.codegen.auxgen import ELPAuxGenerator
from ehex.codegen.rules import (
    facts,
    guessing_rules,
    input_rules,
    checking_rules,
    cardinality_check,
    member_facts,
    subset_check,
)
from ehex.parser.models import asmodel
from ehex.parser.models import elpmodel
from ehex.utils import model

pprender = PositiveProgramGenerator().render
elprender = ELPGenerator().render
asrender = AnswerSetGenerator().render
auxrender = ELPAuxGenerator().render
grrender = GenericReductGenerator().render


def elp_program(elp_model):
    return elprender(elp_model)


def positive_program(elp_model):
    return pprender(elp_model)


def generic_reduct(elp_model):
    return grrender(elp_model)


def answer_set(elements):
    as_model = asmodel.AnswerSet(elements=elements)
    return asrender(as_model)


def guessing_program(ground_atoms, guess_atoms):
    rules = [*guessing_rules(ground_atoms), *facts(ground_atoms | guess_atoms)]
    return auxrender(elpmodel.Program(rules=rules))


def checking_program(ground_atoms, reduct_out):
    rules = [
        *input_rules(),
        *checking_rules(ground_atoms, reduct_out),
    ]
    return auxrender(elpmodel.Program(rules=rules))


def level_check(level, omega):
    cc = cardinality_check(level)
    if omega:
        sc = subset_check(level)
        mr = member_facts(omega)
        rules = [*mr, *sc, *cc]
    else:
        rules = [*cc]
    return auxrender(elpmodel.Program(rules=rules))


def clingo_show_directives(atoms):
    predicates = [
        (model.neg_name(a.name) if a.negation else a.name, len(a.args))
        for a in atoms
    ]
    directives = [f"#show {name}/{arity}." for name, arity in set(predicates)]
    return "\n".join(directives)
