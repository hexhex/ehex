import sys

from ehex.parser import parse_elp_input
from ehex.parser.asparser import parse_answer_sets
from ehex.codegen import render
from ehex.parser.models import auxmodel
from ehex.solver import clingo
from ehex.solver import dlvhex
from ehex.utils import model


class Unsatisfiable(Exception):
    pass


def solve(solver, src, out, cfg, **kws):
    if out and cfg.debug:
        with open(out, "w") as src_file:
            src_file.write(src)
        result = solver.main(str(out), debug=cfg.debug, **kws)
    else:
        result = solver.main(src=src, debug=cfg.debug, **kws)
    return parse_answer_sets(result)


def select_guess(solution):
    elements = [
        e.args[0]
        for e in solution
        if isinstance(e, auxmodel.AuxGuess) and not e.negation
    ]
    return frozenset(elements)


def select_ans(solution):
    elements = [e for e in solution if not isinstance(e, auxmodel.AuxAtom)]
    return frozenset(elements)


def ehex(cfg):
    elp_model = parse_elp_input(*cfg.elp_in or [])
    if cfg.debug:
        with open(cfg.elp_out, "w") as elp_file:
            elp_file.write(render.elp_program(elp_model))
    pp_src = render.positive_program(elp_model)
    pp_as = [*solve(clingo, pp_src, cfg.pp_out, cfg)][0]
    ground_atoms = [
        element for element in pp_as if isinstance(element, auxmodel.AuxGround)
    ]
    positive_envelope = [
        element
        for element in pp_as
        if not isinstance(element, auxmodel.AuxAtom)
    ]
    if cfg.debug:
        print(
            "Ground weak modals:",
            render.answer_set([atom.args[0] for atom in ground_atoms]),
            file=sys.stderr,
        )
        print(
            "Positive envelope:",
            render.answer_set(positive_envelope),
            file=sys.stderr,
        )
    reduct_src = render.generic_reduct(elp_model)
    with cfg.reduct_out.open("w") as reduct_file:
        reduct_file.write(reduct_src)
    g_src = render.guessing_program(ground_atoms, guess_atoms)
    c_src = render.checking_program(ground_atoms, cfg.reduct_out)
    generic_src = "\n\n".join(
        [
            "% Generic Epistemic Redukt",
            reduct_src,
            "% Guessing Program",
            g_src,
            "% Checking Program",
            c_src,
        ]
    )
    pfilter = {
        model.neg_name(atom.name) if atom.negation else atom.name
        for atom in positive_envelope
    }
    pfilter.add(auxmodel.PREFIX + auxmodel.AuxGuess._name)
    omega = set()
    for k in reversed(range(len(ground_atoms) + 1)):
        if 0 == k and omega:
            if cfg.debug:
                print(
                    "Found world view at a higer level,",
                    f"skipping the last level {k}.",
                    file=sys.stderr,
                )
            break

        lp_out = cfg.lp_out.with_suffix(f".{k}.lp")
        lp_src = "\n\n".join(
            [
                f"% {lp_out}",
                generic_src,
                "% Level Specific Constraints",
                render.level_check(k, omega),
            ]
        )

        def solutions():
            for solution in solve(
                dlvhex, lp_src, lp_out, cfg, pfilter=pfilter
            ):
                guess = select_guess(solution)
                omega.add(guess)
                ans = select_ans(solution)
                yield (guess, ans)

        yield (k, solutions())
        if 0 < k == len(ground_atoms) and omega:
            if cfg.debug:
                print(
                    "Found world view at the top level,",
                    "skipping lower levels.",
                    file=sys.stderr,
                )
            break


def format_solutions(level, solutions):
    world_views = {}
    first_guess = None

    def header(n, guess):
        return f"World: {n}@{level}\nModals: {render.answer_set(guess)}"

    for guess, ans in solutions:
        if first_guess is None:
            first_guess = guess
            yield header(1, guess)
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


def main(cfg):
    cfg.setup()

    try:
        satisfiable = False
        for level, solutions in ehex(cfg):
            for line in format_solutions(level, solutions):
                print(line)
                satisfiable = True
        if not satisfiable:
            raise Unsatisfiable
    except Unsatisfiable:
        cfg.cleanup()
        raise

    cfg.cleanup()
