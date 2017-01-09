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

from grako.buffering import Buffer
from grako.parsing import graken, Parser
from grako.util import re, RE_FLAGS, generic_main  # noqa


__all__ = [
    'EHEXParser',
    'EHEXSemantics',
    'main'
]

KEYWORDS = {}


class EHEXBuffer(Buffer):
    def __init__(
        self,
        text,
        whitespace=re.compile('[ \\t\\n]+', RE_FLAGS | re.DOTALL),
        nameguard=None,
        comments_re='%\\*((?:.|\\n)*?)\\*%',
        eol_comments_re='%([^*][^\\n]*?)?$',
        ignorecase=None,
        namechars='',
        **kwargs
    ):
        super(EHEXBuffer, self).__init__(
            text,
            whitespace=whitespace,
            nameguard=nameguard,
            comments_re=comments_re,
            eol_comments_re=eol_comments_re,
            ignorecase=ignorecase,
            namechars=namechars,
            **kwargs
        )


class EHEXParser(Parser):
    def __init__(
        self,
        whitespace=re.compile('[ \\t\\n]+', RE_FLAGS | re.DOTALL),
        nameguard=None,
        comments_re='%\\*((?:.|\\n)*?)\\*%',
        eol_comments_re='%([^*][^\\n]*?)?$',
        ignorecase=None,
        left_recursion=False,
        parseinfo=True,
        keywords=None,
        namechars='',
        buffer_class=EHEXBuffer,
        **kwargs
    ):
        if keywords is None:
            keywords = KEYWORDS
        super(EHEXParser, self).__init__(
            whitespace=whitespace,
            nameguard=nameguard,
            comments_re=comments_re,
            eol_comments_re=eol_comments_re,
            ignorecase=ignorecase,
            left_recursion=left_recursion,
            parseinfo=parseinfo,
            keywords=keywords,
            namechars=namechars,
            buffer_class=buffer_class,
            **kwargs
        )

    @graken()
    def _start_(self):
        self._program_()
        self._check_eof()

    @graken('Program')
    def _program_(self):
        with self._optional():
            self._statements_()
            self.name_last_node('statements')
        with self._optional():
            self._query_()
            self.name_last_node('query')
        self.ast._define(
            ['query', 'statements'],
            []
        )

    @graken()
    def _statements_(self):

        def block0():
            self._statement_()
        self._closure(block0)

    @graken()
    def _statement_(self):
        with self._choice():
            with self._option():
                self._constraint_()
            with self._option():
                self._rule_()
            with self._option():
                self._weak_constraint_()
            with self._option():
                self._optimize_()
            self._error('no available options')

    @graken('Constraint')
    def _constraint_(self):
        self._CONS_()
        self._cut()
        with self._optional():
            self._body_()
            self.name_last_node('body')
        self._DOT_()
        self.ast._define(
            ['body'],
            []
        )

    @graken('Rule')
    def _rule_(self):
        self._head_()
        self.name_last_node('head')
        with self._optional():
            self._CONS_()
            with self._optional():
                self._body_()
                self.name_last_node('body')
        self._DOT_()
        self.ast._define(
            ['body', 'head'],
            []
        )

    @graken('WeakConstraint')
    def _weak_constraint_(self):
        self._WCONS_()
        with self._optional():
            self._body_()
            self.name_last_node('body')
        self._DOT_()
        self._SQUARE_OPEN_()
        self._weight_at_level_()
        self.name_last_node('weight_at_level')
        self._SQUARE_CLOSE_()
        self.ast._define(
            ['body', 'weight_at_level'],
            []
        )

    @graken()
    def _head_(self):
        with self._choice():
            with self._option():
                self._disjunction_()
            with self._option():
                self._choice_()
            self._error('no available options')

    @graken('RuleBody')
    def _body_(self):

        def sep1():
            with self._group():
                self._COMMA_()

        def block1():
            with self._choice():
                with self._option():
                    self._extended_literal_()
                with self._option():
                    self._aggregate_literal_()
                self._error('no available options')
        self._positive_closure(block1, sep=sep1)
        self.name_last_node('literals')
        self.ast._define(
            ['literals'],
            []
        )

    @graken('Disjunction')
    def _disjunction_(self):

        def sep1():
            with self._group():
                self._OR_()

        def block1():
            self._classical_literal_()
        self._positive_closure(block1, sep=sep1)
        self.name_last_node('literals')
        self.ast._define(
            ['literals'],
            []
        )

    @graken('ChoiceRelation')
    def _choice_(self):
        with self._choice():
            with self._option():
                self._term_()
                self.name_last_node('left')
                self._relational_op_()
                self.name_last_node('left_op')
                self._choice_set_()
                self.name_last_node('choices')
                with self._optional():
                    self._relational_op_()
                    self.name_last_node('right_op')
                    self._term_()
                    self.name_last_node('right')
            with self._option():
                self._choice_set_()
                self.name_last_node('choices')
                with self._optional():
                    self._relational_op_()
                    self.name_last_node('right_op')
                    self._term_()
                    self.name_last_node('right')
            self._error('no available options')
        self.ast._define(
            ['choices', 'left', 'left_op', 'right', 'right_op'],
            []
        )

    @graken()
    def _choice_set_(self):
        self._CURLY_OPEN_()
        self._choice_elements_()
        self.name_last_node('@')
        self._CURLY_CLOSE_()

    @graken()
    def _choice_elements_(self):

        def sep0():
            with self._group():
                self._SEMICOLON_()

        def block0():
            self._choice_element_()
        self._positive_closure(block0, sep=sep0)

    @graken('ChoiceElement')
    def _choice_element_(self):
        self._classical_literal_()
        self.name_last_node('choice')
        with self._optional():
            self._COLON_()
            with self._optional():
                self._extended_literals_()
                self.name_last_node('literals')
        self.ast._define(
            ['choice', 'literals'],
            []
        )

    @graken()
    def _aggregate_literal_(self):
        with self._choice():
            with self._option():
                self._default_negated_aggreagate_()
            with self._option():
                self._aggregate_()
            self._error('no available options')

    @graken('DefaultNegation')
    def _default_negated_aggreagate_(self):
        self._NOT_()
        self.name_last_node('op')
        self._aggregate_()
        self.name_last_node('literal')
        self.ast._define(
            ['literal', 'op'],
            []
        )

    @graken('AggregateRelation')
    def _aggregate_(self):
        with self._choice():
            with self._option():
                self._term_()
                self.name_last_node('left')
                self._relational_op_()
                self.name_last_node('left_op')
                self._aggregate_function_()
                self.name_last_node('aggregate')
                with self._optional():
                    self._relational_op_()
                    self.name_last_node('right_op')
                    self._term_()
                    self.name_last_node('right')
            with self._option():
                self._aggregate_function_()
                self.name_last_node('aggregate')
                self._relational_op_()
                self.name_last_node('right_op')
                self._term_()
                self.name_last_node('right')
            self._error('no available options')
        self.ast._define(
            ['aggregate', 'left', 'left_op', 'right', 'right_op'],
            []
        )

    @graken('AggregateFunction')
    def _aggregate_function_(self):
        self._aggregate_function_symbol_()
        self.name_last_node('symbol')
        self._CURLY_OPEN_()
        with self._optional():
            with self._ifnot():
                self._CURLY_CLOSE_()
            self._aggregate_elements_()
            self.name_last_node('elements')
        self._CURLY_CLOSE_()
        self.ast._define(
            ['elements', 'symbol'],
            []
        )

    @graken()
    def _aggregate_function_symbol_(self):
        with self._choice():
            with self._option():
                self._AGGREGATE_COUNT_()
            with self._option():
                self._AGGREGATE_MAX_()
            with self._option():
                self._AGGREGATE_MIN_()
            with self._option():
                self._AGGREGATE_SUM_()
            self._error('no available options')

    @graken()
    def _aggregate_elements_(self):

        def sep0():
            with self._group():
                self._SEMICOLON_()

        def block0():
            self._aggregate_element_()
        self._positive_closure(block0, sep=sep0)

    @graken('AggregateElement')
    def _aggregate_element_(self):
        with self._optional():
            self._terms_()
            self.name_last_node('terms')
        with self._optional():
            self._COLON_()
            with self._optional():
                self._extended_literals_()
                self.name_last_node('literals')
        self.ast._define(
            ['literals', 'terms'],
            []
        )

    @graken('Optimize')
    def _optimize_(self):
        self._optimize_function_()
        self.name_last_node('function')
        self._CURLY_OPEN_()
        with self._optional():
            self._optimize_elements_()
            self.name_last_node('elements')
        self._CURLY_CLOSE_()
        self._DOT_()
        self.ast._define(
            ['elements', 'function'],
            []
        )

    @graken()
    def _optimize_function_(self):
        with self._choice():
            with self._option():
                self._MAXIMIZE_()
            with self._option():
                self._MINIMIZE_()
            self._error('no available options')

    @graken()
    def _optimize_elements_(self):

        def sep0():
            with self._group():
                self._SEMICOLON_()

        def block0():
            self._optimize_element_()
        self._positive_closure(block0, sep=sep0)

    @graken('OptimizeElement')
    def _optimize_element_(self):
        self._weight_at_level_()
        self.name_last_node('weight_at_level')
        with self._optional():
            self._COLON_()
            with self._optional():
                self._extended_literals_()
                self.name_last_node('literals')
        self.ast._define(
            ['literals', 'weight_at_level'],
            []
        )

    @graken('Query')
    def _query_(self):
        self._classical_literal_()
        self.name_last_node('literal')
        self._QUERY_MARK_()
        self.ast._define(
            ['literal'],
            []
        )

    @graken()
    def _classical_literal_(self):
        with self._choice():
            with self._option():
                self._strong_negated_atom_()
            with self._option():
                self._atom_()
            self._error('no available options')

    @graken('Atom')
    def _atom_(self):
        self._predicate_symbol_()
        self.name_last_node('symbol')
        with self._optional():
            self._PAREN_OPEN_()
            with self._optional():
                self._terms_()
                self.name_last_node('arguments')
            self._PAREN_CLOSE_()
        self.ast._define(
            ['arguments', 'symbol'],
            []
        )

    @graken('StrongNegation')
    def _strong_negated_atom_(self):
        with self._group():
            with self._choice():
                with self._option():
                    self._MINUS_()
                with self._option():
                    self._token('¬')
                self._error('expecting one of: ¬')
        self.name_last_node('op')
        self._atom_()
        self.name_last_node('atom')
        self.ast._define(
            ['atom', 'op'],
            []
        )

    @graken()
    def _predicate_symbol_(self):
        with self._ifnot():
            self._NOT_()
        self._ID_()

    @graken()
    def _builtin_atom_(self):
        with self._choice():
            with self._option():
                self._arithmetic_atom_()
            with self._option():
                self._binary_relation_()
            self._error('no available options')

    @graken('Conjunction')
    def _extended_literals_(self):
        with self._group():

            def sep1():
                with self._group():
                    self._COMMA_()

            def block1():
                self._extended_literal_()
            self._positive_closure(block1, sep=sep1)
        self.name_last_node('literals')
        self.ast._define(
            ['literals'],
            []
        )

    @graken()
    def _extended_literal_(self):
        with self._choice():
            with self._option():
                self._default_negated_literal_()
            with self._option():
                self._modal_literal_()
            with self._option():
                self._classical_literal_()
            with self._option():
                self._builtin_atom_()
            self._error('no available options')

    @graken('DefaultNegation')
    def _default_negated_literal_(self):
        self._NOT_()
        self.name_last_node('op')
        with self._group():
            with self._choice():
                with self._option():
                    self._modal_literal_()
                with self._option():
                    self._classical_literal_()
                with self._option():
                    self._builtin_atom_()
                self._error('no available options')
        self.name_last_node('literal')
        self.ast._define(
            ['literal', 'op'],
            []
        )

    @graken('WeighAtLevel')
    def _weight_at_level_(self):
        self._term_()
        self.name_last_node('weight')
        with self._optional():
            self._AT_()
            self._term_()
            self.name_last_node('level')
        with self._optional():
            self._COMMA_()
            self._terms_()
            self.name_last_node('terms')
        self.ast._define(
            ['level', 'terms', 'weight'],
            []
        )

    @graken()
    def _terms_(self):

        def sep0():
            with self._group():
                self._COMMA_()

        def block0():
            self._term_()
        self._positive_closure(block0, sep=sep0)

    @graken()
    def _term_(self):
        with self._choice():
            with self._option():
                self._arith_expr_()
            with self._option():
                self._basic_term_()
            self._error('no available options')

    @graken()
    def _arith_expr_(self):
        with self._choice():
            with self._option():
                self._additive_()
            with self._option():
                self._multiplicative_()
            self._error('no available options')

    @graken('AdditiveTerm')
    def _additive_(self):
        self._arith_term_()
        self.add_last_node_to_name('@')

        def block1():
            with self._group():
                with self._choice():
                    with self._option():
                        self._PLUS_()
                    with self._option():
                        self._MINUS_()
                    self._error('no available options')
            self.name_last_node('@')
            self._cut()
            self._arith_term_()
            self.name_last_node('@')
        self._positive_closure(block1)

    @graken()
    def _arith_term_(self):
        with self._choice():
            with self._option():
                self._multiplicative_()
            with self._option():
                self._basic_term_()
            self._error('no available options')

    @graken('MultiplicativeTerm')
    def _multiplicative_(self):
        self._arith_factor_()
        self.add_last_node_to_name('@')

        def block1():
            with self._group():
                with self._choice():
                    with self._option():
                        self._TIMES_()
                    with self._option():
                        self._DIV_()
                    self._error('no available options')
            self.name_last_node('@')
            self._cut()
            self._arith_factor_()
            self.name_last_node('@')
        self._positive_closure(block1)

    @graken()
    def _arith_factor_(self):
        self._basic_term_()

    @graken()
    def _basic_term_(self):
        with self._choice():
            with self._option():
                self._subterm_()
            with self._option():
                self._negative_term_()
            with self._option():
                self._functional_()
            with self._option():
                self._constant_()
            with self._option():
                self._variable_()
            self._error('no available options')

    @graken('FunctionalTerm')
    def _functional_(self):
        self._function_symbol_()
        self.name_last_node('symbol')
        self._PAREN_OPEN_()
        with self._optional():
            self._terms_()
            self.name_last_node('arguments')
        self._PAREN_CLOSE_()
        self.ast._define(
            ['arguments', 'symbol'],
            []
        )

    @graken()
    def _function_symbol_(self):
        self._ID_()

    @graken('SubTerm')
    def _subterm_(self):
        self._PAREN_OPEN_()
        self._term_()
        self.name_last_node('@')
        self._PAREN_CLOSE_()

    @graken('NegativeTerm')
    def _negative_term_(self):
        self._MINUS_()
        self._term_()

    @graken('ConstantTerm')
    def _constant_(self):
        with self._choice():
            with self._option():
                self._STRING_()
            with self._option():
                self._ID_()
            with self._option():
                self._NUMBER_()
            self._error('no available options')

    @graken('VariableTerm')
    def _variable_(self):
        with self._choice():
            with self._option():
                self._VARIABLE_()
            with self._option():
                self._ANONYMOUS_VARIABLE_()
            self._error('no available options')

    @graken()
    def _relational_op_(self):
        with self._choice():
            with self._option():
                self._LESS_OR_EQ_()
            with self._option():
                self._GREATER_OR_EQ_()
            with self._option():
                self._UNEQUAL_()
            with self._option():
                self._EQUAL_()
            with self._option():
                self._LESS_()
            with self._option():
                self._GREATER_()
            self._error('no available options')

    @graken()
    def _ID_(self):
        with self._ifnot():
            self._token('aux__')
        self._pattern(r'[a-z][a-zA-Z0-9_]*')

    @graken()
    def _VARIABLE_(self):
        with self._ifnot():
            self._token('AUX__')
        self._pattern(r'[A-Z][a-zA-Z0-9_]*')

    @graken('str')
    def _STRING_(self):
        self._pattern(r'"(\\"|[^"])*"')

    @graken('int')
    def _NUMBER_(self):
        self._pattern(r'0|\d+')

    @graken()
    def _ANONYMOUS_VARIABLE_(self):
        self._token('_')

    @graken()
    def _DOT_(self):
        self._token('.')

    @graken()
    def _COMMA_(self):
        self._token(',')

    @graken()
    def _QUERY_MARK_(self):
        self._token('?')

    @graken()
    def _COLON_(self):
        self._token(':')

    @graken()
    def _SEMICOLON_(self):
        self._token(';')

    @graken()
    def _OR_(self):
        with self._choice():
            with self._option():
                self._token('|')
            with self._option():
                self._token('v')
            self._error('expecting one of: v |')

    @graken()
    def _NOT_(self):
        self._token('not')

    @graken()
    def _CONS_(self):
        with self._choice():
            with self._option():
                self._token(':-')
            with self._option():
                self._token('←')
            self._error('expecting one of: :- ←')

    @graken()
    def _WCONS_(self):
        self._token(':~')

    @graken()
    def _PLUS_(self):
        self._token('+')

    @graken()
    def _MINUS_(self):
        self._token('-')

    @graken()
    def _TIMES_(self):
        self._token('*')

    @graken()
    def _DIV_(self):
        self._token('/')

    @graken()
    def _AT_(self):
        self._token('@')

    @graken()
    def _PAREN_OPEN_(self):
        self._token('(')

    @graken()
    def _PAREN_CLOSE_(self):
        self._token(')')

    @graken()
    def _SQUARE_OPEN_(self):
        self._token('[')

    @graken()
    def _SQUARE_CLOSE_(self):
        self._token(']')

    @graken()
    def _CURLY_OPEN_(self):
        self._token('{')

    @graken()
    def _CURLY_CLOSE_(self):
        self._token('}')

    @graken()
    def _EQUAL_(self):
        self._token('=')

    @graken()
    def _UNEQUAL_(self):
        with self._choice():
            with self._option():
                self._token('<>')
            with self._option():
                self._token('!=')
            self._error('expecting one of: != <>')

    @graken()
    def _LESS_(self):
        self._token('<')

    @graken()
    def _GREATER_(self):
        self._token('>')

    @graken()
    def _LESS_OR_EQ_(self):
        self._token('<=')

    @graken()
    def _GREATER_OR_EQ_(self):
        self._token('>=')

    @graken()
    def _AGGREGATE_COUNT_(self):
        self._token('#count')

    @graken()
    def _AGGREGATE_MAX_(self):
        self._token('#max')

    @graken()
    def _AGGREGATE_MIN_(self):
        self._token('#min')

    @graken()
    def _AGGREGATE_SUM_(self):
        self._token('#sum')

    @graken()
    def _MINIMIZE_(self):
        self._token('#minimi')
        self._pattern(r'[zs]')
        self._token('e')

    @graken()
    def _MAXIMIZE_(self):
        self._token('#maximi')
        self._pattern(r'[zs]')
        self._token('e')

    @graken('Atom')
    def _arithmetic_atom_(self):
        with self._group():
            with self._choice():
                with self._option():
                    self._PLUS_()
                with self._option():
                    self._MINUS_()
                with self._option():
                    self._TIMES_()
                with self._option():
                    self._DIV_()
                with self._option():
                    self._token('#int')
                self._error('expecting one of: #int')
        self.name_last_node('symbol')
        with self._optional():
            self._PAREN_OPEN_()
            with self._optional():
                self._terms_()
                self.name_last_node('arguments')
            self._PAREN_CLOSE_()
        self.ast._define(
            ['arguments', 'symbol'],
            []
        )

    @graken('BinaryRelation')
    def _binary_relation_(self):
        self._term_()
        self.name_last_node('left')
        self._relational_op_()
        self.name_last_node('op')
        self._term_()
        self.name_last_node('right')
        self.ast._define(
            ['left', 'op', 'right'],
            []
        )

    @graken()
    def _modal_literal_(self):
        with self._choice():
            with self._option():
                self._k_modal_()
            with self._option():
                self._m_modal_()
            self._error('no available options')

    @graken('KModal')
    def _k_modal_(self):
        self._token('K')
        self.name_last_node('op')
        self._classical_literal_()
        self.name_last_node('literal')
        self.ast._define(
            ['literal', 'op'],
            []
        )

    @graken('MModal')
    def _m_modal_(self):
        self._token('M')
        self.name_last_node('op')
        self._classical_literal_()
        self.name_last_node('literal')
        self.ast._define(
            ['literal', 'op'],
            []
        )


class EHEXSemantics(object):
    def start(self, ast):
        return ast

    def program(self, ast):
        return ast

    def statements(self, ast):
        return ast

    def statement(self, ast):
        return ast

    def constraint(self, ast):
        return ast

    def rule(self, ast):
        return ast

    def weak_constraint(self, ast):
        return ast

    def head(self, ast):
        return ast

    def body(self, ast):
        return ast

    def disjunction(self, ast):
        return ast

    def choice(self, ast):
        return ast

    def choice_set(self, ast):
        return ast

    def choice_elements(self, ast):
        return ast

    def choice_element(self, ast):
        return ast

    def aggregate_literal(self, ast):
        return ast

    def default_negated_aggreagate(self, ast):
        return ast

    def aggregate(self, ast):
        return ast

    def aggregate_function(self, ast):
        return ast

    def aggregate_function_symbol(self, ast):
        return ast

    def aggregate_elements(self, ast):
        return ast

    def aggregate_element(self, ast):
        return ast

    def optimize(self, ast):
        return ast

    def optimize_function(self, ast):
        return ast

    def optimize_elements(self, ast):
        return ast

    def optimize_element(self, ast):
        return ast

    def query(self, ast):
        return ast

    def classical_literal(self, ast):
        return ast

    def atom(self, ast):
        return ast

    def strong_negated_atom(self, ast):
        return ast

    def predicate_symbol(self, ast):
        return ast

    def builtin_atom(self, ast):
        return ast

    def extended_literals(self, ast):
        return ast

    def extended_literal(self, ast):
        return ast

    def default_negated_literal(self, ast):
        return ast

    def weight_at_level(self, ast):
        return ast

    def terms(self, ast):
        return ast

    def term(self, ast):
        return ast

    def arith_expr(self, ast):
        return ast

    def additive(self, ast):
        return ast

    def arith_term(self, ast):
        return ast

    def multiplicative(self, ast):
        return ast

    def arith_factor(self, ast):
        return ast

    def basic_term(self, ast):
        return ast

    def functional(self, ast):
        return ast

    def function_symbol(self, ast):
        return ast

    def subterm(self, ast):
        return ast

    def negative_term(self, ast):
        return ast

    def constant(self, ast):
        return ast

    def variable(self, ast):
        return ast

    def relational_op(self, ast):
        return ast

    def ID(self, ast):
        return ast

    def VARIABLE(self, ast):
        return ast

    def STRING(self, ast):
        return ast

    def NUMBER(self, ast):
        return ast

    def ANONYMOUS_VARIABLE(self, ast):
        return ast

    def DOT(self, ast):
        return ast

    def COMMA(self, ast):
        return ast

    def QUERY_MARK(self, ast):
        return ast

    def COLON(self, ast):
        return ast

    def SEMICOLON(self, ast):
        return ast

    def OR(self, ast):
        return ast

    def NOT(self, ast):
        return ast

    def CONS(self, ast):
        return ast

    def WCONS(self, ast):
        return ast

    def PLUS(self, ast):
        return ast

    def MINUS(self, ast):
        return ast

    def TIMES(self, ast):
        return ast

    def DIV(self, ast):
        return ast

    def AT(self, ast):
        return ast

    def PAREN_OPEN(self, ast):
        return ast

    def PAREN_CLOSE(self, ast):
        return ast

    def SQUARE_OPEN(self, ast):
        return ast

    def SQUARE_CLOSE(self, ast):
        return ast

    def CURLY_OPEN(self, ast):
        return ast

    def CURLY_CLOSE(self, ast):
        return ast

    def EQUAL(self, ast):
        return ast

    def UNEQUAL(self, ast):
        return ast

    def LESS(self, ast):
        return ast

    def GREATER(self, ast):
        return ast

    def LESS_OR_EQ(self, ast):
        return ast

    def GREATER_OR_EQ(self, ast):
        return ast

    def AGGREGATE_COUNT(self, ast):
        return ast

    def AGGREGATE_MAX(self, ast):
        return ast

    def AGGREGATE_MIN(self, ast):
        return ast

    def AGGREGATE_SUM(self, ast):
        return ast

    def MINIMIZE(self, ast):
        return ast

    def MAXIMIZE(self, ast):
        return ast

    def arithmetic_atom(self, ast):
        return ast

    def binary_relation(self, ast):
        return ast

    def modal_literal(self, ast):
        return ast

    def k_modal(self, ast):
        return ast

    def m_modal(self, ast):
        return ast


def main(filename, startrule, **kwargs):
    with open(filename) as f:
        text = f.read()
    parser = EHEXParser(parseinfo=False)
    return parser.parse(text, startrule, filename=filename, **kwargs)


if __name__ == '__main__':
    import json
    ast = generic_main(main, EHEXParser, name='EHEX')
    print('AST:')
    print(ast)
    print()
    print('JSON:')
    print(json.dumps(ast, indent=2))
    print()
