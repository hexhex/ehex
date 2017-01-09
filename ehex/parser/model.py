#!/usr/bin/env python
# -*- coding: utf-8 -*-

# CAVEAT UTILITOR
#
# This file was automatically generated by Grako.
#
#    https://pypi.python.org/pypi/grako/
#
# Any changes you make to it will be overwritten the next time
# the file is generated.

from __future__ import print_function, division, absolute_import, unicode_literals

from grako.objectmodel import Node
from grako.semantics import ModelBuilderSemantics


class EHEXModelBuilderSemantics(ModelBuilderSemantics):
    def __init__(self):
        types = [
            t for t in globals().values()
            if type(t) is type and issubclass(t, ModelBase)
        ]
        super(EHEXModelBuilderSemantics, self).__init__(types=types)


class ModelBase(Node):
    pass


class Conjunction(ModelBase):
    pass



class Term(ModelBase):
    pass



class Modal(ModelBase):
    pass


class Program(ModelBase):
    def __init__(self,
                 query=None,
                 statements=None,
                 **_kwargs_):
        super(Program, self).__init__(
            query=query,
            statements=statements,
            **_kwargs_
        )


class Constraint(ModelBase):
    def __init__(self,
                 body=None,
                 **_kwargs_):
        super(Constraint, self).__init__(
            body=body,
            **_kwargs_
        )


class Rule(ModelBase):
    def __init__(self,
                 body=None,
                 head=None,
                 **_kwargs_):
        super(Rule, self).__init__(
            body=body,
            head=head,
            **_kwargs_
        )


class WeakConstraint(ModelBase):
    def __init__(self,
                 body=None,
                 weight_at_level=None,
                 **_kwargs_):
        super(WeakConstraint, self).__init__(
            body=body,
            weight_at_level=weight_at_level,
            **_kwargs_
        )


class RuleBody(Conjunction):
    def __init__(self,
                 literals=None,
                 **_kwargs_):
        super(RuleBody, self).__init__(
            literals=literals,
            **_kwargs_
        )


class Disjunction(ModelBase):
    def __init__(self,
                 literals=None,
                 **_kwargs_):
        super(Disjunction, self).__init__(
            literals=literals,
            **_kwargs_
        )


class ChoiceRelation(ModelBase):
    def __init__(self,
                 choices=None,
                 left=None,
                 left_op=None,
                 right=None,
                 right_op=None,
                 **_kwargs_):
        super(ChoiceRelation, self).__init__(
            choices=choices,
            left=left,
            left_op=left_op,
            right=right,
            right_op=right_op,
            **_kwargs_
        )


class ChoiceElement(ModelBase):
    def __init__(self,
                 choice=None,
                 literals=None,
                 **_kwargs_):
        super(ChoiceElement, self).__init__(
            choice=choice,
            literals=literals,
            **_kwargs_
        )


class DefaultNegation(ModelBase):
    def __init__(self,
                 literal=None,
                 op=None,
                 **_kwargs_):
        super(DefaultNegation, self).__init__(
            literal=literal,
            op=op,
            **_kwargs_
        )


class AggregateRelation(ModelBase):
    def __init__(self,
                 aggregate=None,
                 left=None,
                 left_op=None,
                 right=None,
                 right_op=None,
                 **_kwargs_):
        super(AggregateRelation, self).__init__(
            aggregate=aggregate,
            left=left,
            left_op=left_op,
            right=right,
            right_op=right_op,
            **_kwargs_
        )


class AggregateFunction(ModelBase):
    def __init__(self,
                 elements=None,
                 symbol=None,
                 **_kwargs_):
        super(AggregateFunction, self).__init__(
            elements=elements,
            symbol=symbol,
            **_kwargs_
        )


class AggregateElement(ModelBase):
    def __init__(self,
                 literals=None,
                 terms=None,
                 **_kwargs_):
        super(AggregateElement, self).__init__(
            literals=literals,
            terms=terms,
            **_kwargs_
        )


class Optimize(ModelBase):
    def __init__(self,
                 elements=None,
                 function=None,
                 **_kwargs_):
        super(Optimize, self).__init__(
            elements=elements,
            function=function,
            **_kwargs_
        )


class OptimizeElement(ModelBase):
    def __init__(self,
                 literals=None,
                 weight_at_level=None,
                 **_kwargs_):
        super(OptimizeElement, self).__init__(
            literals=literals,
            weight_at_level=weight_at_level,
            **_kwargs_
        )


class Query(ModelBase):
    def __init__(self,
                 literal=None,
                 **_kwargs_):
        super(Query, self).__init__(
            literal=literal,
            **_kwargs_
        )


class Atom(ModelBase):
    def __init__(self,
                 arguments=None,
                 symbol=None,
                 **_kwargs_):
        super(Atom, self).__init__(
            arguments=arguments,
            symbol=symbol,
            **_kwargs_
        )


class StrongNegation(ModelBase):
    def __init__(self,
                 atom=None,
                 op=None,
                 **_kwargs_):
        super(StrongNegation, self).__init__(
            atom=atom,
            op=op,
            **_kwargs_
        )


class WeighAtLevel(ModelBase):
    def __init__(self,
                 level=None,
                 terms=None,
                 weight=None,
                 **_kwargs_):
        super(WeighAtLevel, self).__init__(
            level=level,
            terms=terms,
            weight=weight,
            **_kwargs_
        )


class AdditiveTerm(Term):
    def __init__(self, **_kwargs_):
        super(AdditiveTerm, self).__init__(**_kwargs_)


class MultiplicativeTerm(Term):
    def __init__(self, **_kwargs_):
        super(MultiplicativeTerm, self).__init__(**_kwargs_)


class FunctionalTerm(Term):
    def __init__(self,
                 arguments=None,
                 symbol=None,
                 **_kwargs_):
        super(FunctionalTerm, self).__init__(
            arguments=arguments,
            symbol=symbol,
            **_kwargs_
        )


class SubTerm(Term):
    def __init__(self, **_kwargs_):
        super(SubTerm, self).__init__(**_kwargs_)


class NegativeTerm(Term):
    def __init__(self, **_kwargs_):
        super(NegativeTerm, self).__init__(**_kwargs_)


class ConstantTerm(Term):
    def __init__(self, **_kwargs_):
        super(ConstantTerm, self).__init__(**_kwargs_)


class VariableTerm(Term):
    def __init__(self, **_kwargs_):
        super(VariableTerm, self).__init__(**_kwargs_)


class BinaryRelation(ModelBase):
    def __init__(self,
                 left=None,
                 op=None,
                 right=None,
                 **_kwargs_):
        super(BinaryRelation, self).__init__(
            left=left,
            op=op,
            right=right,
            **_kwargs_
        )


class KModal(Modal):
    def __init__(self,
                 literal=None,
                 op=None,
                 **_kwargs_):
        super(KModal, self).__init__(
            literal=literal,
            op=op,
            **_kwargs_
        )


class MModal(Modal):
    def __init__(self,
                 literal=None,
                 op=None,
                 **_kwargs_):
        super(MModal, self).__init__(
            literal=literal,
            op=op,
            **_kwargs_
        )
