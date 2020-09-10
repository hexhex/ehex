import argparse
import logging
import os
import signal
import sys

from tatsu.exceptions import FailedParse

from ehex.solver import config, ehex
from ehex.utils import solver


def sigterm_handler(sig, *_):
    print(f"Solver terminated by signal {sig}", file=sys.stderr)
    sys.exit(143)


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "elp_in",
        nargs="*",
        metavar="FILE",
        help='input file; read from <stdin> if %(metavar)s="-" or if no '
        "file is given",
    )
    parser.add_argument(
        "-m",
        "--models",
        metavar="N",
        default=0,
        help="limit the number of printed models per world view to %(metavar)s "
        "(N=0 means all) (default is %(default)s)",
    ),
    parser.add_argument(
        "-n",
        "--world-views",
        metavar="N",
        default=1,
        help="limit the number of printed world views to %(metavar)s "
        "(N=0 means all) (default is %(default)s)",
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        metavar="DIR",
        help="output directory for intermediate files (default is  a "
        'temporary directory or "out" in debug mode)',
    )
    parser.add_argument(
        "-c",
        "--compute-consequences",
        action="store_true",
        help="compute brave and cautious consequences to reduce guesswork",
    )
    parser.add_argument(
        "-g",
        "--guessing-hints",
        action="store_true",
        help="add guessing hint rules to optimize guessing",
    )
    parser.add_argument(
        "-r",
        "--ground-reduct",
        action="store_true",
        help="compute a possibly smaller set of ground modal literals "
        "by grounding the generic epistemic reduct",
    )
    parser.add_argument(
        "-p",
        "--planning-mode",
        action="store_true",
        help="enable optimizations specific to planning problems",
    )
    parser.add_argument(
        "-a",
        "--all-optimizations",
        action="store_true",
        help="enable all optimizations, this is equivalent to -cgrp",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="print debug information to <stderr> and write all "
        "intermediate programs to files in the output directory",
    )

    args = parser.parse_args()
    with config.setup(**vars(args)) as cfg:
        logging.basicConfig(
            level=cfg.log_level, format="%(levelname)s %(name)s: %(message)s"
        )
        try:
            ehex.main()
            sys.stdout.flush()
        except BrokenPipeError:
            # https://docs.python.org/3/library/signal.html#note-on-sigpipe
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
            sys.exit(1)
        except KeyboardInterrupt:
            print("Interrupted", file=sys.stderr)
            sys.exit(0)
        except FileNotFoundError as e:
            print(f"File not found: {e}", file=sys.stderr)
            sys.exit(1)
        except FailedParse as e:
            print(f"Parse error: {e}", file=sys.stderr)
            sys.exit(1)
        except solver.Unsatisfiable:
            print("Unsatisfiable", file=sys.stderr)
            sys.exit(0)
        except solver.AssumptionError as e:
            print(f"Assumption error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
