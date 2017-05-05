#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=fixme

"""We apply a variant of the following translation rules from Kahl et al. 2016:

        ┌───────────────┬──────────────┬────────────────────────┐
        │ Modal literal │ Replace with │ Add rules              │
        ├───────────────┼──────────────┼────────────────────────┤
        │ K ℓ           │ not ¬k_ℓ, ℓ  │ ¬k_ℓ ← k0_ℓ.           │
        ├───────────────┼──────────────┤ ¬k_ℓ ← k1_ℓ, not ℓ.    │
        │ not K ℓ       │ ¬k_ℓ         │                        │
        ├───────────────┼──────────────┼────────────────────────┤
        │ M ℓ           │ m_ℓ          │ m_ℓ ← m1_ℓ.            │
        ├───────────────┼──────────────┤ m_ℓ ← m0_ℓ, not not ℓ. │
        │ not M ℓ       │ not m_ℓ      │                        │
        └───────────────┴──────────────┴────────────────────────┘

Kahl, P. T., Leclerc, A. P., & Son, T. C. (2016). A Parallel Memory-efficient
Epistemic Logic Program Solver: Harder, Better, Faster. Retrieved from
http://arxiv.org/abs/1608.06910
"""

from copy import copy
from functools import wraps

from grako.model import NodeWalker

from ehex import inject
from ehex.parser import model
from ehex.parser.model import EHEXModelBuilderSemantics as EHEXSemantics
from ehex.parser.ehex import EHEXParser
from ehex import SNEG_PREFIX
from ehex.utils import is_iterable


class TransformationWalker(NodeWalker):

    @staticmethod
    def clone(node, ast=None, **kwargs):
        attrs = {}
        if ast is None:
            ast = copy(node.ast)
            attrs = {
                key: value
                for key, value in vars(node).items()
                if not key.startswith('_')
            }
        attrs.update(kwargs)
        return type(node)(ast=ast, **attrs)

    def walk_object(self, node):
        if is_iterable(node):
            return self.walk_iterable(node)
        return copy(node)

    def walk_iterable(self, node):
        walked_list = []
        for child in node:
            walked = self.walk(child)
            if walked is not None:
                walked_list.append(walked)
        return walked_list

    def walk_Node(self, node):
        walked = {
            key: self.walk(child)
            for key, child in vars(node).items()
            if not key.startswith('_')
        } or self.walk(node.ast)
        return self.clone(node, ast=walked)


def postwalk(fn):
    @wraps(fn)
    def walk(self, node):
        node = self.walk_Node(node)
        return fn(self, node)
    return walk


class RewriteStrongNegationWalker(TransformationWalker):

    def __init__(self):
        self._predicates = set()

    @postwalk
    def walk_StrongNegation(self, node):
        atom = node.atom
        arity = len(atom.arguments or ())
        self._predicates.add((atom.symbol, arity))
        symbol = inject.aux_name(atom.symbol, SNEG_PREFIX)
        return self.clone(atom, symbol=symbol)

    @postwalk
    def walk_Program(self, node):
        node.statements += self._new_constraints()
        return node

    def _new_constraints(self):
        for symbol, arity in self._predicates:
            if arity <= 3:
                terms = ['X', 'Y', 'Z'][:arity]
            else:
                terms = ['V{}'.format(i + 1) for i in range(arity)]
            vars_ = [inject.variable(x) for x in terms]
            positive = inject.atom(symbol, vars_)
            negated = inject.sn_atom(symbol, vars_)
            yield inject.constraint([positive, negated])


class OverApproximationWalker(TransformationWalker):

    def __init__(self):
        self._new_rules = []

    @staticmethod
    def walk_Constraint(*_):
        return None

    @staticmethod
    def walk_WeakConstraint(*_):
        return None

    @staticmethod
    def walk_Optimize(*_):
        return None

    @staticmethod
    def walk_Query(*_):
        return None

    @staticmethod
    def walk_DefaultNegation(*_):
        # This does not work in some cases, e.g., kahl/ex17.ehex:
        # if isinstance(node.literal, model.MModal):
        #     return self.clone(
        #         node,
        #         literal=self.walk_Node(node.literal.literal)
        #     )
        return None

    @staticmethod
    def walk_MModal(*_):
        return None

    @postwalk
    def walk_KModal(self, node, *_):
        return node.literal

    @staticmethod
    def walk_AggregateRelation(*_):
        return None

    @postwalk
    def walk_RuleBody(self, node, *_):
        if not node.literals:
            return None
        return node

    @postwalk
    def walk_Rule(self, node, *_):
        head = node.head
        if isinstance(head, model.Disjunction):
            for literal in head.literals:
                self._new_rules.append(
                    inject.rule(literal, node.body)
                )
            return None
        elif isinstance(head, model.ChoiceRelation):
            for element in head.choices:
                self._new_rules.append(
                    inject.rule(
                        element.choice,
                        node.body.literals + element.literals.literals
                    )
                )
            return None

        return node

    @postwalk
    def walk_Program(self, node, *_):
        node.statements += self._new_rules
        return node


class TranslationWalker(TransformationWalker):
    """Translate epistemic ASP program to HEX program"""

    def __init__(self):
        self.modals = set()

    @postwalk
    def walk_KModal(self, node):  # pylint: disable=no-self-use
        modal_literal = inject.not_k_literal(node.literal)
        return inject.conjunction([
            inject.not_(modal_literal),
            node.literal
        ])

    @postwalk
    def walk_MModal(self, node):  # pylint: disable=no-self-use
        return inject.m_literal(node.literal)

    @postwalk
    def walk_DefaultNegation(self, node):  # pylint: disable=no-self-use
        if isinstance(node.literal, model.Conjunction):
            return node.literal.literals[0].literal
        return node


class RenameAtomsWalker(TransformationWalker):
    """Rename all atoms in a program"""

    def __init__(self, rename_function=None):
        self.rename = rename_function or self._rename

    @staticmethod
    def _rename(old):
        return '{}_'.format(old)

    @postwalk
    def walk_Atom(self, node):  # pylint: disable=no-self-use
        if node.symbol.startswith('#'):
            return node
        new_symbol = self.rename(node.symbol)
        return self.clone(node, symbol=new_symbol)
