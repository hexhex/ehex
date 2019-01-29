import argparse
import pathlib
import signal
import sys
from ehex.ehexsolver import Solver, Context
from ehex import KAHL_SEMANTICS, SE_SEMANTICS


def sigterm_handler(sig, *_):
    print('Solver terminated by signal {}'.format(sig), file=sys.stderr)
    sys.exit(143)


class GrounderAction(argparse.Action):
    CHOICES = ['asp', 'pen']
    E1 = 'unknown grounder: {} (choose from {})'
    E2 = 'duplicate value: {}'

    def __call__(self, parser, namespace, values, option_string=None):
        grounder = set()
        for value in values:
            if value not in self.CHOICES:
                choices = ', '.join(repr(value) for value in self.CHOICES)
                message = self.E1.format(repr(value), choices)
                raise argparse.ArgumentError(self, message)
            if value in grounder:
                message = (self.E2.format(repr(value)))
                raise argparse.ArgumentError(self, message)
            grounder.add(value)
        setattr(namespace, self.dest, grounder)


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)

    parser = argparse.ArgumentParser(description='EHEX solver.')
    parser.add_argument('ehex_in', metavar='EHEX_FILE', type=pathlib.Path)
    parser.add_argument(
        '--reduct-out', metavar='REDUCT_FILE', type=pathlib.Path
    )
    parser.add_argument(
        '--guessing-out', metavar='GUESSING_FILE', type=pathlib.Path
    )
    parser.add_argument(
        '--envelope-out', metavar='ENVELOPE_FILE', type=pathlib.Path
    )
    parser.add_argument('--level-out', metavar='LEVEL_FILE', type=pathlib.Path)
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-g', '--grounder', nargs='+', action=GrounderAction)
    parser.add_argument('-m', '--max-level', type=int)
    parser.add_argument('-o', '--optimize-guessing', action='store_true')
    parser.add_argument('-p', '--planning-mode', action='store_true')
    parser.add_argument('-q', '--enable-queries', action='store_true')
    parser.add_argument(
        '-k', '--kahl-semantics', action='store_const', const=KAHL_SEMANTICS,
        default=SE_SEMANTICS, dest='semantics'
    )
    parser.add_argument('-w', '--one-world-view', action='store_true')
    options = parser.parse_args()

    if options.reduct_out is None:
        options.reduct_out = options.ehex_in.with_suffix('.hex')
    if options.guessing_out is None:
        options.guessing_out = options.ehex_in.with_suffix('.guess.hex')
    if options.envelope_out is None:
        options.envelope_out = options.ehex_in.with_suffix('.envelope.hex')
    if options.level_out is None:
        options.level_out = options.ehex_in.with_suffix('.level.hex')

    solver = Solver(Context(options))
    solver.solve(options)


if __name__ == '__main__':
    main()
