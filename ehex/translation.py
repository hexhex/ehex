#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""We apply a variant of the following translation rules from Kahl et al. 2016:

        ┌───────────────┬──────────────┬─────────────────────────┐
        │ Modal literal │ Replace with │ Add rules               │
        ├───────────────┼──────────────┼─────────────────────────┤
        │ K ℓ           │ not ¬k_ℓ, ℓ  │ ¬k_ℓ ← k0_ℓ.            │
        ├───────────────┼──────────────┤ ¬k_ℓ ← k1_ℓ, not ℓ.     │
        │ not K ℓ       │ ¬k_ℓ         │                         │
        ├───────────────┼──────────────┼─────────────────────────┤
        │ M ℓ           │ m_ℓ          │ m_ℓ ← m1_ℓ.             │
        ├───────────────┼──────────────┤ m_ℓ ← m0_ℓ, [not not]ℓ. │
        │ not M ℓ       │ not m_ℓ      │                         │
        └───────────────┴──────────────┴─────────────────────────┘

Kahl, P. T., Leclerc, A. P., & Son, T. C. (2016). A Parallel Memory-efficient
Epistemic Logic Program Solver: Harder, Better, Faster. Retrieved from
http://arxiv.org/abs/1608.06910

The double negation is turned off by default and can be enabled using the flag
--kahl-semantics on the command line.
"""

import re
from copy import copy
from functools import wraps

from tatsu.model import NodeWalker

from ehex import fragments
from ehex.filter import ExtendedModals
from ehex.parser import model
from ehex import SNEG_PREFIX, AUX_MARKER, K_PREFIX, M_PREFIX, DOMAIN
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
                if not key.startswith("_")
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
            if not key.startswith("_")
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
        symbol = fragments.aux_name(atom.symbol, SNEG_PREFIX)
        return self.clone(atom, symbol=symbol)

    @postwalk
    def walk_Program(self, node):
        node.statements += self._new_constraints()
        return node

    def _new_constraints(self):
        for symbol, arity in self._predicates:
            if arity <= 3:
                terms = ["X", "Y", "Z"][:arity]
            else:
                terms = ["V{}".format(i + 1) for i in range(arity)]
            vars_ = [fragments.variable(x) for x in terms]
            positive = fragments.atom(symbol, vars_)
            negated = fragments.sn_atom(symbol, vars_)
            yield fragments.constraint([positive, negated])


class OverApproximationWalker(TransformationWalker):
    def __init__(self):
        self._new_rules = []

    def walk_Constraint(self, node, *_):
        literals = ExtendedModals(node)
        node = self.walk_Node(node)
        self._add_domain(literals, node)

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
        return None

    @staticmethod
    def walk_MModal(*_):
        return None

    @postwalk
    def walk_KModal(self, node, *_):
        return node.literal

    def walk_AggregateRelation(self, node, *_):
        if node.left_op and node.right_op:
            node = fragments.conjunction(
                [
                    self.clone(node, right_op=None, right=None),
                    self.clone(node, left_op=None, left=None),
                ]
            )
        elif "=" not in (node.left_op, node.right_op):
            return None
        return self.walk_Node(node)

    def walk_BinaryRelation(self, node, *_):
        if node.op == "=":
            return self.walk_Node(node)
        return None

    @postwalk
    def walk_RuleBody(self, node, *_):
        if not node.literals:
            return None
        return node

    def _add_domain(self, literals, node):
        for literal in literals:
            if isinstance(literal, model.DefaultNegation):
                modal = literal.literal
            else:
                modal = literal
            self._new_rules.append(
                fragments.rule(fragments.domain_atom(modal), node.body)
            )

    def walk_Rule(self, node, *_):
        literals = ExtendedModals(node)
        node = self.walk_Node(node)
        self._add_domain(literals, node)

        head = node.head
        if isinstance(head, model.Disjunction):
            for literal in head.literals:
                self._new_rules.append(fragments.rule(literal, node.body))
            return None
        if isinstance(head, model.ChoiceRelation):
            for element in head.choices:
                self._new_rules.append(
                    fragments.rule(
                        element.choice, node.body.literals + element.literals.literals
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

    def __init__(self, semantics):
        self.semantics = semantics
        self.modals = []

    @postwalk
    def walk_KModal(self, node):  # pylint: disable=no-self-use
        self.modals.append(node)
        modal_literal = fragments.not_k_literal(node.literal)
        return fragments.conjunction([fragments.not_(modal_literal), node.literal])

    @postwalk
    def walk_MModal(self, node):  # pylint: disable=no-self-use
        self.modals.append(node)
        return fragments.m_literal(node.literal)

    @postwalk
    def walk_AggregateRelation(self, node, *_):
        if node.left_op and node.right_op:
            return fragments.conjunction(
                [
                    self.clone(node, right_op=None, right=None),
                    self.clone(node, left_op=None, left=None),
                ]
            )
        return node

    def walk_DefaultNegation(self, node):  # pylint: disable=no-self-use
        walked = self.walk_Node(node)
        if isinstance(walked.literal, model.Conjunction):
            if isinstance(node.literal, model.KModal):
                return walked.literal.literals[0].literal
            if isinstance(node.literal, model.AggregateRelation):
                return fragments.conjunction(
                    [fragments.not_(aggr) for aggr in walked.literal.literals]
                )
        return walked

    @postwalk
    def walk_Program(self, node):
        node.statements.extend(
            fragments.guessing_assignment_rules(self.modals, self.semantics)
        )
        return node


class GroundingResultWalker(TransformationWalker):
    DOM_ATOM = re.compile(
        "{}{}_({}|{})_({}_)?(.+)".format(
            AUX_MARKER, DOMAIN, K_PREFIX, M_PREFIX, SNEG_PREFIX,
        )
    ).match

    @classmethod
    def walk_Atom(cls, node, *_):
        match = cls.DOM_ATOM(node.symbol)
        if not match:
            return node
        op, sneg, symbol = match.groups()
        literal = model.Atom(symbol=symbol, arguments=node.arguments)
        if sneg:
            literal = model.StrongNegation(atom=literal)
        if op == K_PREFIX:
            literal = model.KModal(literal=literal, op="K")
        else:
            literal = model.MModal(literal=literal, op="M")
        return literal

    @staticmethod
    def walk_StrongNegation(node, *_):
        return node


class RenameAtomsWalker(TransformationWalker):
    """Rename all atoms in a program"""

    def __init__(self, rename_function=None):
        self.rename = rename_function or self._rename

    @staticmethod
    def _rename(old):
        return "{}_".format(old)

    @postwalk
    def walk_Atom(self, node):  # pylint: disable=no-self-use
        if node.symbol.startswith("#"):
            return node
        new_symbol = self.rename(node.symbol)
        return self.clone(node, symbol=new_symbol)
