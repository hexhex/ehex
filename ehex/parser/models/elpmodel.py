#!/usr/bin/env python
# -*- coding: utf-8 -*-

# CAVEAT UTILITOR
#
# This file was automatically generated by TatSu.
#
#    https://pypi.python.org/pypi/tatsu/
#
# Any changes you make to it will be overwritten the next time
# the file is generated.

from __future__ import generator_stop

from tatsu.objectmodel import Node
from tatsu.semantics import ModelBuilderSemantics


class ModelBase(Node):
    pass


class ELPModelBuilderSemantics(ModelBuilderSemantics):
    def __init__(self, context=None, types=None):
        types = [
            t for t in globals().values()
            if type(t) is type and issubclass(t, ModelBase)
        ] + (types or [])
        super(ELPModelBuilderSemantics, self).__init__(context=context, types=types)

class Term(ModelBase):
    pass


class Program(ModelBase):
    rules = None


class Rule(ModelBase):
    body = None
    head = None


class Disjunction(ModelBase):
    atoms = None


class StandardLiteral(ModelBase):
    atom = None
    negation = None


class Atom(ModelBase):
    args = None
    name = None
    negation = None


class BuiltinAtom(ModelBase):
    left = None
    rel = None
    right = None


class ChoiceAtom(ModelBase):
    elements = None
    left = None
    left_rel = None
    right = None
    right_rel = None


class ChoiceElement(ModelBase):
    atom = None
    literals = None


class AggregateLiteral(ModelBase):
    atom = None
    negation = None


class AggregateAtom(ModelBase):
    elements = None
    left = None
    left_rel = None
    name = None
    right = None
    right_rel = None


class AggregateElement(ModelBase):
    literals = None
    terms = None


class IntervalTerm(Term):
    pass


class ArithmeticTerm(Term):
    pass


class FunctionalTerm(Term):
    args = None
    name = None


class SubTerm(Term):
    pass


class NegativeTerm(Term):
    pass


class ConstantTerm(Term):
    pass


class VariableTerm(Term):
    pass


class ModalLiteral(ModelBase):
    literal = None
    modality = None
    negation = None
