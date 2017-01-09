#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections

from grako.model import NodeWalker
from ehex.codegen import EHEXCodeGenerator as CodeGenerator


render = CodeGenerator().render


class NodeFilter(NodeWalker):
    def __init__(self, node):
        self.node = node

    def __iter__(self):
        return self.walk(self.node)

    def walk(self, node):
        iterable = super(NodeFilter, self).walk(node)
        if iterable is not None:
            return iterable
        if (isinstance(node, collections.Iterable)
                and not isinstance(node, str)):
            return self.walk_iterable(node)
        return iter([])

    def walk_iterable(self, node):
        for child in node:
            for item in self.walk(child):
                yield item

    def walk_Node(self, node, *_, **__):
        for child in node.children_list():
            for item in self.walk(child):
                yield item


class Modals(NodeFilter):

    @staticmethod
    def walk_Modal(node):
        yield node


class Variables(NodeFilter):

    @staticmethod
    def walk_VariableTerm(node):
        yield node


class Atoms(NodeFilter):

    @staticmethod
    def walk_Atom(node):
        yield node


class Terms(NodeFilter):

    @staticmethod
    def walk_Term(node, *_, **__):
        yield node


class DefaultNegations(NodeFilter):

    @staticmethod
    def walk_DefaultNegation(node, *_, **__):
        yield node


class StrongNegations(NodeFilter):

    @staticmethod
    def walk_StrongNegation(node, *_, **__):
        yield node


class ExtendedLiterals(DefaultNegations, Modals, StrongNegations, Atoms):
    pass
