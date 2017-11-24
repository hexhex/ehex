# EHEX Solver

Installation as user:

```
$ pip3 install --user git+https://github.com/hexhex/ehex.git
```

Installation as root:

```
$ sudo pip3 install git+https://github.com/hexhex/ehex.git
```

You will also need `dlvhex2` and `clingo` (see below). After installation you can use the provided `ehex` command line tool. Basic usage with examples from this repository:

```
$ git clone https://github.com/hexhex/ehex.git
$ cd ehex
$ ehex examples/eligible.ehex
```

Dependencies: Python 3.4+, [Grako](https://bitbucket.org/apalala/grako); also make sure `dlvhex2` with the [NestedHexPlugin](https://github.com/hexhex/nestedhexplugin) and `clingo` 5.2.x is in your path.
