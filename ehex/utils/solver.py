from collections import namedtuple

from ehex.codegen import render
from ehex.parser import asparser
from ehex.parser.models import auxmodel
from ehex.solver import clingo
from ehex.solver.config import cfg


class Unsatisfiable(Exception):
    pass


class Satisfiable(Exception):
    pass


class AssumptionError(RuntimeError):
    pass


Facts = namedtuple(
    "Facts",
    ["ground", "guess_true", "guess_false", "guess"],
    defaults=[frozenset(), frozenset(), frozenset()],
)

Context = namedtuple("Context", ["guess_size", "omega", "level"])


def solve(solver, src, out=None, parse=asparser.parse, **kws):
    if out and cfg.debug:
        with open(out, "w") as src_file:
            src_file.write(src)
        result = solver.main(str(out), **kws)
    else:
        result = solver.main(src=src, **kws)

    return parse(result)


def compute_envelope(elp):
    pp_src = render.positive_program(elp)
    atoms = frozenset(next(solve(clingo, pp_src, out=cfg.path.pp_out)))
    ground_atoms = frozenset(
        atom for atom in atoms if isinstance(atom, auxmodel.AuxGround)
    )
    return atoms - ground_atoms, Facts(ground_atoms)


def split_solution(solution):
    atoms = frozenset(solution)
    guess = frozenset(
        atom for atom in atoms if isinstance(atom, auxmodel.AuxGuess)
    )
    return guess, atoms - guess


def format_solutions(evaluation_level, solutions):
    world_views = {}
    first_guess = None

    def header(count, guess):
        modals = frozenset(atom.args[0] for atom in guess)
        return f"World: {count}@{evaluation_level}\nModal literals: {render.answer_set(modals)}"

    for guess, ans in solutions:
        if first_guess is None:
            first_guess = guess
            yield header(1, guess)
            if cfg.sat_mode:
                continue
        if guess == first_guess:
            yield render.answer_set(ans)
        else:
            world_view = world_views.setdefault(guess, [])
            world_view.append(ans)
    if not first_guess:
        return
    for i, (guess, world_view) in enumerate(world_views.items()):
        yield header(i + 2, guess)
        for ans in world_view:
            yield render.answer_set(ans)
