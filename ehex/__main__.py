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

    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument(
        "elp_in",
        nargs="*",
        metavar="FILE",
        help="""input file; read from <stdin> if %(metavar)s is '-' or if
        no file is given""",
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        metavar="DIR",
        help="""base directory for intermediate files (default is  a
        temporary directory or 'out' in debug mode)""",
    )
    parser.add_argument(
        "-c",
        "--compute-consequences",
        action="store_true",
        help="compute brave and cautious consequences to reduce guesswork",
    )
    parser.add_argument(
        "-gh",
        "--guessing-hints",
        action="store_true",
        help="add guessing hint rules to optimize guessing",
    )
    parser.add_argument(
        "-gr",
        "--ground-reduct",
        action="store_true",
        help="""compute a possibly smaller set of ground modal literals
        by grounding the generic epistemic reduct""",
    )
    parser.add_argument(
        "-p",
        "--planning-mode",
        action="store_true",
        help="enable optimizations specific to planning problems",
    )
    parser.add_argument(
        "-s",
        "--sat-mode",
        action="store_true",
        help="check if input is satisfiable and exit; implies -c",
    )
    parser.add_argument(
        "-rs",
        "--reduct-semantics",
        choices=config.ASP_SEMANTICS,
        type=str.upper,
        help="""select the ASP semantics to be used for the Epistemic
        Reduct: the choice 'FLP' corresponds to the FLP answer set
        semantics, and the choice 'NEX' corresponds to the answer set
        semantics of programs with nested expressions, i.e., expressions
        of the form 'not not a' over an atom 'a' (default is FLP)""",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="""set log level to DEBUG  and write generated intermediate
        programs to files in the specified output directory""",
    )

    args = parser.parse_args()
    with config.setup(**vars(args)) as cfg:
        logging.basicConfig(
            level=cfg.log_level, format="%(levelname)s %(name)s: %(message)s"
        )
        try:
            ehex.main()
            sys.stdout.flush()
        except solver.Satisfiable:
            print("Satisfiable")
            sys.exit(0)
        except solver.Unsatisfiable:
            print("Unsatisfiable")
            sys.exit(0)
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
        except solver.AssumptionError as e:
            print(f"Assumption error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
