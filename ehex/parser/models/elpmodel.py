#!/usr/bin/env python

# CAVEAT UTILITOR
#
# This file was automatically generated by TatSu.
#
#    https://pypi.python.org/pypi/tatsu/
#
# Any changes you make to it will be overwritten the next time
# the file is generated.

from __future__ import annotations

from typing import Any
from dataclasses import dataclass

from tatsu.objectmodel import Node
from tatsu.semantics import ModelBuilderSemantics


@dataclass(eq=False)
class ModelBase(Node):
    pass


class ELPModelBuilderSemantics(ModelBuilderSemantics):
    def __init__(self, context=None, types=None):
        types = [
            t for t in globals().values()
            if type(t) is type and issubclass(t, ModelBase)
        ] + (types or [])
        super(ELPModelBuilderSemantics, self).__init__(context=context, types=types)

@dataclass(eq=False)
class Term(ModelBase):
    pass


@dataclass(eq=False)
class Program(ModelBase):
    rules: Any = None


@dataclass(eq=False)
class Rule(ModelBase):
    body: Any = None
    head: Any = None


@dataclass(eq=False)
class Disjunction(ModelBase):
    atoms: Any = None


@dataclass(eq=False)
class StandardLiteral(ModelBase):
    atom: Any = None
    negation: Any = None


@dataclass(eq=False)
class Atom(ModelBase):
    args: Any = None
    name: Any = None
    negation: Any = None


@dataclass(eq=False)
class BuiltinAtom(ModelBase):
    left: Any = None
    rel: Any = None
    right: Any = None


@dataclass(eq=False)
class ChoiceAtom(ModelBase):
    elements: Any = None
    left: Any = None
    left_rel: Any = None
    right: Any = None
    right_rel: Any = None


@dataclass(eq=False)
class ChoiceElement(ModelBase):
    atom: Any = None
    literals: Any = None


@dataclass(eq=False)
class AggregateLiteral(ModelBase):
    atom: Any = None
    negation: Any = None


@dataclass(eq=False)
class AggregateAtom(ModelBase):
    elements: Any = None
    left: Any = None
    left_rel: Any = None
    name: Any = None
    right: Any = None
    right_rel: Any = None


@dataclass(eq=False)
class AggregateElement(ModelBase):
    literals: Any = None
    terms: Any = None


@dataclass(eq=False)
class IntervalTerm(Term):
    pass


@dataclass(eq=False)
class ArithmeticTerm(Term):
    pass


@dataclass(eq=False)
class FunctionalTerm(Term):
    args: Any = None
    name: Any = None


@dataclass(eq=False)
class SubTerm(Term):
    pass


@dataclass(eq=False)
class NegativeTerm(Term):
    pass


@dataclass(eq=False)
class ConstantTerm(Term):
    pass


@dataclass(eq=False)
class VariableTerm(Term):
    pass


@dataclass(eq=False)
class ModalLiteral(ModelBase):
    literal: Any = None
    modality: Any = None
    negation: Any = None
