import hashlib
import pathlib
import sys
import tempfile
import types

from ehex.parser import parse_elp_input
from ehex.parser.asparser import parse_answer_sets
from ehex.codegen import render
from ehex.parser.models import auxmodel
from ehex.solver import clingo
from ehex.solver import dlvhex
from ehex.utils import model


def solve(reasoner, src, out, cfg, **kws):
    if cfg.debug:
        with open(out, "w") as src_file:
            src_file.write(src)
        result = reasoner.main(str(out), debug=cfg.debug, **kws)
    else:
        result = reasoner.main(src=src, debug=cfg.debug, **kws)
    return parse_answer_sets(result)


def select_guess(solution):
    elements = [
        e.args[0]
        for e in solution
        if isinstance(e, auxmodel.AuxGuess) and not e.negation
    ]
    return frozenset(elements)


def select_as(solution):
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
    g_src = render.guessing_program(ground_atoms)
    c_src = render.consistency_check(ground_atoms, cfg.reduct_out)
    with cfg.reduct_out.open("w") as reduct_file:
        reduct_file.write(reduct_src)
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
        lp_src = render.level_check(k, omega)
        lp_out = cfg.lp_out.with_suffix(f".{k}.lp")
        lp_src = "\n\n".join(
            [
                f"% {lp_out}",
                generic_src,
                "% Level Specific Constraints",
                lp_src,
            ]
        )

        def solutions():
            for solution in solve(
                dlvhex, lp_src, lp_out, cfg, pfilter=pfilter
            ):
                guess = select_guess(solution)
                omega.add(guess)
                ans = select_as(solution)
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


class Config(types.SimpleNamespace):
    debug = False
    out_dir = None

    def setup_paths(self):
        if self.debug or self.out_dir:
            run_dir = "".join(sorted(self.elp_in))
            run_dir = hashlib.sha1(run_dir.encode()).hexdigest()[:7]
            run_dir = pathlib.Path(self.out_dir or "out") / run_dir
            run_dir.mkdir(exist_ok=True, parents=True)
        else:
            self.tmp_dir = tempfile.TemporaryDirectory()
            run_dir = pathlib.Path(self.tmp_dir.name)

        self.reduct_out = run_dir / "reduct.lp"
        self.pp_out = run_dir / "positive.lp"
        self.lp_out = run_dir / "level.lp"
        self.elp_out = run_dir / "parsed.elp"
        if self.debug:
            print(f"Runtime directory: {run_dir}", file=sys.stderr)

    def cleanup(self):
        try:
            self.tmp_dir.cleanup()
        except AttributeError:
            pass


def main(cfg):
    cfg.setup_paths()

    for level, solutions in ehex(cfg):
        for line in format_solutions(level, solutions):
            print(line)

    cfg.cleanup()
