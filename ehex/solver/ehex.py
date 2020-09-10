from ehex.codegen import render
from ehex.parser import elpinput
from ehex.parser.models import auxmodel
from ehex.solver import dlvhex, optimize
from ehex.solver.config import cfg
from ehex.utils import logging, model, solver

logger = logging.get_logger(__name__)


def solve(omega, src, out, pfilter, guess_true_facts=None):
    for solution in solver.solve(dlvhex, src, out=out, pfilter=pfilter):
        guess, ans = solver.split_solution(solution)
        omega.add(guess)
        if guess_true_facts:
            guess = guess.union(guess_true_facts)
        yield (guess, ans)


def ehex():
    elp = elpinput.parse(*cfg.elp_in or [])
    atoms, facts = solver.compute_envelope(elp)

    if cfg.debug:
        with open(cfg.path.elp_out, "w") as elp_file:
            elp_file.write(render.elprender(elp))

        modals = frozenset(atom.args[0] for atom in facts.ground)
        logger.debug("Ground weak modals: {}", render.answer_set(modals))
        logger.debug("Positive envelope: {}", render.answer_set(atoms))

    if cfg.compute_consequences:
        facts = optimize.with_consequences(elp, facts)

    initial_guess_true_facts = facts.guess_true

    if cfg.ground_reduct:
        facts = optimize.with_reduct(elp, facts)

    if cfg.planning_mode:
        try:
            horizon = next(
                int(a.args[0]) for a in atoms if a.name == "horizon"
            )
        except (StopIteration, ValueError):
            raise solver.AssumptionError(
                "expected an atom of the form 'horizon(N)' in the input program"
            )
        min_size = max_size = horizon + 1
    else:
        min_size = 0
        max_size = len(facts.ground)
    omega = frozenset()
    pfilter = {
        model.neg_name(atom.name) if atom.negation else atom.name
        for atom in atoms
    }
    pfilter.add(auxmodel.AuxGuess.name)

    for guess_size in range(max_size, min_size - 1, -1):
        level = guess_size + len(initial_guess_true_facts)
        logger.debug("Evaluation level: {}", level)

        if omega and guess_size == min_size:
            logger.debug(
                "Found one or more world views at a higer level, {} {}",
                "skipping the last level",
                level,
            )
            break

        context = solver.Context(guess_size, omega, level)

        if cfg.compute_consequences:
            try:
                k_facts = optimize.with_consequences(
                    elp, facts, context=context
                )
            except solver.Unsatisfiable:
                logger.debug("Unsatisfiable at level: {}", level)
                continue
        else:
            k_facts = facts

        lp_out = cfg.path.lp_out.with_suffix(f".{level}.lp")
        reduct_out = cfg.path.reduct_out.with_suffix(f".{level}.lp")
        reduct_src = render.generic_reduct(
            elp, facts.guess_true, facts.guess_false
        )
        with reduct_out.open("w") as reduct_file:
            reduct_file.write(reduct_src)

        lp_src = render.level_program(
            elp,
            k_facts,
            context,
            reduct_out,
            guess_true_facts=k_facts.guess_true - facts.guess_true,
        )

        k_omega = set()
        yield (
            level,
            solve(
                k_omega,
                lp_src,
                lp_out,
                pfilter,
                guess_true_facts=initial_guess_true_facts,
            ),
        )
        if k_omega:
            omega = omega.union(k_omega)
            logger.info(
                "Found {} world view(s) at level {}", len(k_omega), level
            )
        else:
            logger.info("No world view found at level {}", level)

        if omega and min_size < guess_size == max_size:
            logger.debug(
                "Found world view at the top level, skipping lower levels"
            )
            break


def main():
    satisfiable = False
    for level, solutions in ehex():
        for line in solver.format_solutions(level, solutions):
            print(line, file=cfg.stdout)
            satisfiable = True
    if not satisfiable:
        raise solver.Unsatisfiable
