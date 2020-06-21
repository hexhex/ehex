import argparse
import os
import pathlib
import signal
import sys

from ehex.ehexsolver import Solver, Context
from ehex import KAHL_SEMANTICS, SE_SEMANTICS


def sigterm_handler(sig, *_):
    print("Solver terminated by signal {}".format(sig), file=sys.stderr)
    sys.exit(143)


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)

    parser = argparse.ArgumentParser(description="EHEX solver.")
    parser.add_argument("ehex_in", metavar="EHEX_FILE", type=pathlib.Path)
    parser.add_argument("--reduct-out", metavar="REDUCT_FILE", type=pathlib.Path)
    parser.add_argument("--guessing-out", metavar="GUESSING_FILE", type=pathlib.Path)
    parser.add_argument("--envelope-out", metavar="ENVELOPE_FILE", type=pathlib.Path)
    parser.add_argument("--level-out", metavar="LEVEL_FILE", type=pathlib.Path)
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-g", "--grounder", choices=["asp", "pen"], default="pen")
    parser.add_argument("-m", "--max-level", type=int)
    parser.add_argument("-o", "--optimize-guessing", action="store_true")
    parser.add_argument("-p", "--planning-mode", action="store_true")
    parser.add_argument("-q", "--enable-queries", action="store_true")
    parser.add_argument(
        "-k",
        "--kahl-semantics",
        action="store_const",
        const=KAHL_SEMANTICS,
        default=SE_SEMANTICS,
        dest="semantics",
    )
    parser.add_argument("-w", "--witness", action="store_true")
    options = parser.parse_args()

    if options.reduct_out is None:
        options.reduct_out = options.ehex_in.with_suffix(".reduct.lp")
    if options.guessing_out is None:
        options.guessing_out = options.ehex_in.with_suffix(".guessing.hex")
    if options.envelope_out is None:
        options.envelope_out = options.ehex_in.with_suffix(".envelope.lp")
    if options.level_out is None:
        options.level_out = options.ehex_in.with_suffix(".level.lp")

    solver = Solver(Context(options))

    # https://docs.python.org/3/library/signal.html#note-on-sigpipe
    try:
        solver.solve(options)
        sys.stdout.flush()
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)


if __name__ == "__main__":
    main()
