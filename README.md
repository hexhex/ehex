# Epistemic Logic Program Solver Using HEX Programs

Ehex is a prototype solver for problems encoded as *epistemic logic programs* (ELP). ELP programs extend the language of ordinary logic programs with modal operators as in modal logic. The solver includes a parser for ELP programs, which supports the traditional syntax of modal literals on top of the [ASP-Core-2](https://www.mat.unical.it/aspcomp2013/files/ASP-CORE-2.03b.pdf) syntax. It outputs the _world views_ of a given ELP program that correspond to the solutions of the problem to be solved. For computing world views, the solver uses HEX programs containing [_external atoms_](http://www.kr.tuwien.ac.at/staff/tkren/pub/2012/inap2011-nestedhex.pdf), which are used for consistency checking during the evaluation of the HEX programs by reasoning over certain subprograms.

## Installation

The solver is implemented as a command line application written in Python and can be installed with pip from this repository. To install _ehex_ into your local file system run:
```
pip install --user git+https://github.com/hexhex/ehex/
```

Ehex depends on Python >= 3.8 and the [TatSu](https://github.com/neogeny/TatSu) grammar compiler >= 5.0, which is installed as a dependency when pip is used. For reasoning tasks it requires recent binaries of [clingo](https://github.com/potassco/clingo) and [dlvhex2](https://github.com/hexhex/core) in one of the user's PATH directories. Additionally the [dlvhex-nestedhexplugin](https://github.com/hexhex/nestedhexplugin) must be installed.

## Usage

The solver reads input from the files given as command line arguments or from stdin. For more information, type `ehex -h`.

Example:
```sh
$ echo "a :- M a." | ehex
World: 1@1
Modals: {M a}
{a}
```
Some example programs are included in the [examples](examples) directory.

## Development Status

The solver is still under development and some optimizations are missing, which were already implemented in an earlier implementation [draft](https://github.com/hexhex/ehex/releases/tag/draft).

