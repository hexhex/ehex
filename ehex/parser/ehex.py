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


from __future__ import print_function, division, absolute_import, unicode_literals

import sys

from tatsu.buffering import Buffer
from tatsu.parsing import Parser
from tatsu.parsing import tatsumasu
from tatsu.util import re, generic_main  # noqa


KEYWORDS = {}  # type: ignore


class EHEXBuffer(Buffer):
    def __init__(
        self,
        text,
        whitespace=re.compile('[ \\t\\n]+'),
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
        whitespace=re.compile('[ \\t\\n]+'),
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

    @tatsumasu()
    def _start_(self):  # noqa
        self._program_()
        self._check_eof()

    @tatsumasu('Program')
    def _program_(self):  # noqa
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

    @tatsumasu()
    def _statements_(self):  # noqa

        def block0():
            self._statement_()
        self._closure(block0)

    @tatsumasu()
    def _statement_(self):  # noqa
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

    @tatsumasu('Constraint')
    def _constraint_(self):  # noqa
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

    @tatsumasu('Rule')
    def _rule_(self):  # noqa
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

    @tatsumasu('WeakConstraint')
    def _weak_constraint_(self):  # noqa
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

    @tatsumasu()
    def _head_(self):  # noqa
        with self._choice():
            with self._option():
                self._disjunction_()
            with self._option():
                self._choice_()
            self._error('no available options')

    @tatsumasu('RuleBody')
    def _body_(self):  # noqa

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
        self._positive_gather(block1, sep1)
        self.name_last_node('literals')
        self.ast._define(
            ['literals'],
            []
        )

    @tatsumasu('Disjunction')
    def _disjunction_(self):  # noqa

        def sep1():
            with self._group():
                self._OR_()

        def block1():
            self._classical_literal_()
        self._positive_gather(block1, sep1)
        self.name_last_node('literals')
        self.ast._define(
            ['literals'],
            []
        )

    @tatsumasu('ChoiceRelation')
    def _choice_(self):  # noqa
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

    @tatsumasu()
    def _choice_set_(self):  # noqa
        self._CURLY_OPEN_()
        self._choice_elements_()
        self.name_last_node('@')
        self._CURLY_CLOSE_()

    @tatsumasu()
    def _choice_elements_(self):  # noqa

        def sep0():
            with self._group():
                self._SEMICOLON_()

        def block0():
            self._choice_element_()
        self._positive_gather(block0, sep0)

    @tatsumasu('ChoiceElement')
    def _choice_element_(self):  # noqa
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

    @tatsumasu()
    def _aggregate_literal_(self):  # noqa
        with self._choice():
            with self._option():
                self._default_negated_aggreagate_()
            with self._option():
                self._aggregate_()
            self._error('no available options')

    @tatsumasu('DefaultNegation')
    def _default_negated_aggreagate_(self):  # noqa
        self._NOT_()
        self.name_last_node('op')
        self._aggregate_()
        self.name_last_node('literal')
        self.ast._define(
            ['literal', 'op'],
            []
        )

    @tatsumasu('AggregateRelation')
    def _aggregate_(self):  # noqa
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

    @tatsumasu('AggregateFunction')
    def _aggregate_function_(self):  # noqa
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

    @tatsumasu()
    def _aggregate_function_symbol_(self):  # noqa
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

    @tatsumasu()
    def _aggregate_elements_(self):  # noqa

        def sep0():
            with self._group():
                self._SEMICOLON_()

        def block0():
            self._aggregate_element_()
        self._positive_gather(block0, sep0)

    @tatsumasu('AggregateElement')
    def _aggregate_element_(self):  # noqa
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

    @tatsumasu('Optimize')
    def _optimize_(self):  # noqa
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

    @tatsumasu()
    def _optimize_function_(self):  # noqa
        with self._choice():
            with self._option():
                self._MAXIMIZE_()
            with self._option():
                self._MINIMIZE_()
            self._error('no available options')

    @tatsumasu()
    def _optimize_elements_(self):  # noqa

        def sep0():
            with self._group():
                self._SEMICOLON_()

        def block0():
            self._optimize_element_()
        self._positive_gather(block0, sep0)

    @tatsumasu('OptimizeElement')
    def _optimize_element_(self):  # noqa
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

    @tatsumasu('Query')
    def _query_(self):  # noqa
        self._classical_literal_()
        self.name_last_node('literal')
        self._QUERY_MARK_()
        self.ast._define(
            ['literal'],
            []
        )

    @tatsumasu()
    def _classical_literal_(self):  # noqa
        with self._choice():
            with self._option():
                self._strong_negated_atom_()
            with self._option():
                self._atom_()
            self._error('no available options')

    @tatsumasu('Atom')
    def _atom_(self):  # noqa
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

    @tatsumasu('StrongNegation')
    def _strong_negated_atom_(self):  # noqa
        with self._group():
            with self._choice():
                with self._option():
                    self._MINUS_()
                with self._option():
                    self._token('¬')
                self._error('no available options')
        self.name_last_node('op')
        self._atom_()
        self.name_last_node('atom')
        self.ast._define(
            ['atom', 'op'],
            []
        )

    @tatsumasu()
    def _predicate_symbol_(self):  # noqa
        with self._ifnot():
            self._NOT_()
        self._ID_()

    @tatsumasu()
    def _builtin_atom_(self):  # noqa
        with self._choice():
            with self._option():
                self._arithmetic_atom_()
            with self._option():
                self._binary_relation_()
            self._error('no available options')

    @tatsumasu('Conjunction')
    def _extended_literals_(self):  # noqa
        with self._group():

            def sep1():
                with self._group():
                    self._COMMA_()

            def block1():
                self._extended_literal_()
            self._positive_gather(block1, sep1)
        self.name_last_node('literals')
        self.ast._define(
            ['literals'],
            []
        )

    @tatsumasu()
    def _extended_literal_(self):  # noqa
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

    @tatsumasu('DefaultNegation')
    def _default_negated_literal_(self):  # noqa
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

    @tatsumasu('WeighAtLevel')
    def _weight_at_level_(self):  # noqa
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

    @tatsumasu()
    def _terms_(self):  # noqa

        def sep0():
            with self._group():
                self._COMMA_()

        def block0():
            self._term_()
        self._positive_gather(block0, sep0)

    @tatsumasu()
    def _term_(self):  # noqa
        with self._choice():
            with self._option():
                self._interval_()
            with self._option():
                self._arith_expr_()
            with self._option():
                self._basic_term_()
            self._error('no available options')

    @tatsumasu()
    def _arith_expr_(self):  # noqa
        with self._choice():
            with self._option():
                self._additive_()
            with self._option():
                self._multiplicative_()
            self._error('no available options')

    @tatsumasu('AdditiveTerm')
    def _additive_(self):  # noqa
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

    @tatsumasu()
    def _arith_term_(self):  # noqa
        with self._choice():
            with self._option():
                self._multiplicative_()
            with self._option():
                self._basic_term_()
            self._error('no available options')

    @tatsumasu('MultiplicativeTerm')
    def _multiplicative_(self):  # noqa
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

    @tatsumasu()
    def _arith_factor_(self):  # noqa
        self._basic_term_()

    @tatsumasu()
    def _basic_term_(self):  # noqa
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

    @tatsumasu('Interval')
    def _interval_(self):  # noqa
        with self._group():
            with self._choice():
                with self._option():
                    self._arith_expr_()
                with self._option():
                    self._basic_term_()
                self._error('no available options')
        self.name_last_node('left')
        self._token('..')
        self._cut()
        self._term_()
        self.name_last_node('right')
        self.ast._define(
            ['left', 'right'],
            []
        )

    @tatsumasu('FunctionalTerm')
    def _functional_(self):  # noqa
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

    @tatsumasu()
    def _function_symbol_(self):  # noqa
        self._ID_()

    @tatsumasu('SubTerm')
    def _subterm_(self):  # noqa
        self._PAREN_OPEN_()
        self._term_()
        self.name_last_node('@')
        self._PAREN_CLOSE_()

    @tatsumasu('NegativeTerm')
    def _negative_term_(self):  # noqa
        self._MINUS_()
        self._term_()

    @tatsumasu('ConstantTerm')
    def _constant_(self):  # noqa
        with self._choice():
            with self._option():
                self._STRING_()
            with self._option():
                self._ID_()
            with self._option():
                self._NUMBER_()
            self._error('no available options')

    @tatsumasu('VariableTerm')
    def _variable_(self):  # noqa
        with self._choice():
            with self._option():
                self._VARIABLE_()
            with self._option():
                self._ANONYMOUS_VARIABLE_()
            self._error('no available options')

    @tatsumasu()
    def _relational_op_(self):  # noqa
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

    @tatsumasu()
    def _ID_(self):  # noqa
        with self._ifnot():
            self._token('aux__')
        self._pattern(r'[a-z][a-zA-Z0-9_]*')

    @tatsumasu()
    def _VARIABLE_(self):  # noqa
        with self._ifnot():
            self._token('AUX__')
        self._pattern(r'[A-Z][a-zA-Z0-9_]*')

    @tatsumasu('str')
    def _STRING_(self):  # noqa
        self._pattern(r'"(\\"|[^"])*"')

    @tatsumasu('int')
    def _NUMBER_(self):  # noqa
        self._pattern(r'0|\d+')

    @tatsumasu()
    def _ANONYMOUS_VARIABLE_(self):  # noqa
        self._token('_')

    @tatsumasu()
    def _DOT_(self):  # noqa
        self._token('.')

    @tatsumasu()
    def _COMMA_(self):  # noqa
        self._token(',')

    @tatsumasu()
    def _QUERY_MARK_(self):  # noqa
        self._token('?')

    @tatsumasu()
    def _COLON_(self):  # noqa
        self._token(':')

    @tatsumasu()
    def _SEMICOLON_(self):  # noqa
        self._token(';')

    @tatsumasu()
    def _OR_(self):  # noqa
        with self._choice():
            with self._option():
                self._token('|')
            with self._option():
                self._token('v')
            self._error('no available options')

    @tatsumasu()
    def _NOT_(self):  # noqa
        self._token('not')

    @tatsumasu()
    def _CONS_(self):  # noqa
        with self._choice():
            with self._option():
                self._token(':-')
            with self._option():
                self._token('←')
            self._error('no available options')

    @tatsumasu()
    def _WCONS_(self):  # noqa
        self._token(':~')

    @tatsumasu()
    def _PLUS_(self):  # noqa
        self._token('+')

    @tatsumasu()
    def _MINUS_(self):  # noqa
        self._token('-')

    @tatsumasu()
    def _TIMES_(self):  # noqa
        self._token('*')

    @tatsumasu()
    def _DIV_(self):  # noqa
        self._token('/')

    @tatsumasu()
    def _AT_(self):  # noqa
        self._token('@')

    @tatsumasu()
    def _PAREN_OPEN_(self):  # noqa
        self._token('(')

    @tatsumasu()
    def _PAREN_CLOSE_(self):  # noqa
        self._token(')')

    @tatsumasu()
    def _SQUARE_OPEN_(self):  # noqa
        self._token('[')

    @tatsumasu()
    def _SQUARE_CLOSE_(self):  # noqa
        self._token(']')

    @tatsumasu()
    def _CURLY_OPEN_(self):  # noqa
        self._token('{')

    @tatsumasu()
    def _CURLY_CLOSE_(self):  # noqa
        self._token('}')

    @tatsumasu()
    def _EQUAL_(self):  # noqa
        self._token('=')

    @tatsumasu()
    def _UNEQUAL_(self):  # noqa
        with self._choice():
            with self._option():
                self._token('<>')
            with self._option():
                self._token('!=')
            self._error('no available options')

    @tatsumasu()
    def _LESS_(self):  # noqa
        self._token('<')

    @tatsumasu()
    def _GREATER_(self):  # noqa
        self._token('>')

    @tatsumasu()
    def _LESS_OR_EQ_(self):  # noqa
        self._token('<=')

    @tatsumasu()
    def _GREATER_OR_EQ_(self):  # noqa
        self._token('>=')

    @tatsumasu()
    def _AGGREGATE_COUNT_(self):  # noqa
        self._token('#count')

    @tatsumasu()
    def _AGGREGATE_MAX_(self):  # noqa
        self._token('#max')

    @tatsumasu()
    def _AGGREGATE_MIN_(self):  # noqa
        self._token('#min')

    @tatsumasu()
    def _AGGREGATE_SUM_(self):  # noqa
        self._token('#sum')

    @tatsumasu()
    def _MINIMIZE_(self):  # noqa
        self._token('#minimi')
        self._pattern(r'[zs]')
        self._token('e')

    @tatsumasu()
    def _MAXIMIZE_(self):  # noqa
        self._token('#maximi')
        self._pattern(r'[zs]')
        self._token('e')

    @tatsumasu('Atom')
    def _arithmetic_atom_(self):  # noqa
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
                self._error('no available options')
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

    @tatsumasu('BinaryRelation')
    def _binary_relation_(self):  # noqa
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

    @tatsumasu()
    def _modal_literal_(self):  # noqa
        with self._choice():
            with self._option():
                self._k_modal_()
            with self._option():
                self._m_modal_()
            self._error('no available options')

    @tatsumasu('KModal')
    def _k_modal_(self):  # noqa
        self._token('K')
        self.name_last_node('op')
        self._classical_literal_()
        self.name_last_node('literal')
        self.ast._define(
            ['literal', 'op'],
            []
        )

    @tatsumasu('MModal')
    def _m_modal_(self):  # noqa
        self._token('M')
        self.name_last_node('op')
        self._classical_literal_()
        self.name_last_node('literal')
        self.ast._define(
            ['literal', 'op'],
            []
        )


class EHEXSemantics(object):
    def start(self, ast):  # noqa
        return ast

    def program(self, ast):  # noqa
        return ast

    def statements(self, ast):  # noqa
        return ast

    def statement(self, ast):  # noqa
        return ast

    def constraint(self, ast):  # noqa
        return ast

    def rule(self, ast):  # noqa
        return ast

    def weak_constraint(self, ast):  # noqa
        return ast

    def head(self, ast):  # noqa
        return ast

    def body(self, ast):  # noqa
        return ast

    def disjunction(self, ast):  # noqa
        return ast

    def choice(self, ast):  # noqa
        return ast

    def choice_set(self, ast):  # noqa
        return ast

    def choice_elements(self, ast):  # noqa
        return ast

    def choice_element(self, ast):  # noqa
        return ast

    def aggregate_literal(self, ast):  # noqa
        return ast

    def default_negated_aggreagate(self, ast):  # noqa
        return ast

    def aggregate(self, ast):  # noqa
        return ast

    def aggregate_function(self, ast):  # noqa
        return ast

    def aggregate_function_symbol(self, ast):  # noqa
        return ast

    def aggregate_elements(self, ast):  # noqa
        return ast

    def aggregate_element(self, ast):  # noqa
        return ast

    def optimize(self, ast):  # noqa
        return ast

    def optimize_function(self, ast):  # noqa
        return ast

    def optimize_elements(self, ast):  # noqa
        return ast

    def optimize_element(self, ast):  # noqa
        return ast

    def query(self, ast):  # noqa
        return ast

    def classical_literal(self, ast):  # noqa
        return ast

    def atom(self, ast):  # noqa
        return ast

    def strong_negated_atom(self, ast):  # noqa
        return ast

    def predicate_symbol(self, ast):  # noqa
        return ast

    def builtin_atom(self, ast):  # noqa
        return ast

    def extended_literals(self, ast):  # noqa
        return ast

    def extended_literal(self, ast):  # noqa
        return ast

    def default_negated_literal(self, ast):  # noqa
        return ast

    def weight_at_level(self, ast):  # noqa
        return ast

    def terms(self, ast):  # noqa
        return ast

    def term(self, ast):  # noqa
        return ast

    def arith_expr(self, ast):  # noqa
        return ast

    def additive(self, ast):  # noqa
        return ast

    def arith_term(self, ast):  # noqa
        return ast

    def multiplicative(self, ast):  # noqa
        return ast

    def arith_factor(self, ast):  # noqa
        return ast

    def basic_term(self, ast):  # noqa
        return ast

    def interval(self, ast):  # noqa
        return ast

    def functional(self, ast):  # noqa
        return ast

    def function_symbol(self, ast):  # noqa
        return ast

    def subterm(self, ast):  # noqa
        return ast

    def negative_term(self, ast):  # noqa
        return ast

    def constant(self, ast):  # noqa
        return ast

    def variable(self, ast):  # noqa
        return ast

    def relational_op(self, ast):  # noqa
        return ast

    def ID(self, ast):  # noqa
        return ast

    def VARIABLE(self, ast):  # noqa
        return ast

    def STRING(self, ast):  # noqa
        return ast

    def NUMBER(self, ast):  # noqa
        return ast

    def ANONYMOUS_VARIABLE(self, ast):  # noqa
        return ast

    def DOT(self, ast):  # noqa
        return ast

    def COMMA(self, ast):  # noqa
        return ast

    def QUERY_MARK(self, ast):  # noqa
        return ast

    def COLON(self, ast):  # noqa
        return ast

    def SEMICOLON(self, ast):  # noqa
        return ast

    def OR(self, ast):  # noqa
        return ast

    def NOT(self, ast):  # noqa
        return ast

    def CONS(self, ast):  # noqa
        return ast

    def WCONS(self, ast):  # noqa
        return ast

    def PLUS(self, ast):  # noqa
        return ast

    def MINUS(self, ast):  # noqa
        return ast

    def TIMES(self, ast):  # noqa
        return ast

    def DIV(self, ast):  # noqa
        return ast

    def AT(self, ast):  # noqa
        return ast

    def PAREN_OPEN(self, ast):  # noqa
        return ast

    def PAREN_CLOSE(self, ast):  # noqa
        return ast

    def SQUARE_OPEN(self, ast):  # noqa
        return ast

    def SQUARE_CLOSE(self, ast):  # noqa
        return ast

    def CURLY_OPEN(self, ast):  # noqa
        return ast

    def CURLY_CLOSE(self, ast):  # noqa
        return ast

    def EQUAL(self, ast):  # noqa
        return ast

    def UNEQUAL(self, ast):  # noqa
        return ast

    def LESS(self, ast):  # noqa
        return ast

    def GREATER(self, ast):  # noqa
        return ast

    def LESS_OR_EQ(self, ast):  # noqa
        return ast

    def GREATER_OR_EQ(self, ast):  # noqa
        return ast

    def AGGREGATE_COUNT(self, ast):  # noqa
        return ast

    def AGGREGATE_MAX(self, ast):  # noqa
        return ast

    def AGGREGATE_MIN(self, ast):  # noqa
        return ast

    def AGGREGATE_SUM(self, ast):  # noqa
        return ast

    def MINIMIZE(self, ast):  # noqa
        return ast

    def MAXIMIZE(self, ast):  # noqa
        return ast

    def arithmetic_atom(self, ast):  # noqa
        return ast

    def binary_relation(self, ast):  # noqa
        return ast

    def modal_literal(self, ast):  # noqa
        return ast

    def k_modal(self, ast):  # noqa
        return ast

    def m_modal(self, ast):  # noqa
        return ast


def main(filename, start=None, **kwargs):
    if start is None:
        start = 'start'
    if not filename or filename == '-':
        text = sys.stdin.read()
    else:
        with open(filename) as f:
            text = f.read()
    parser = EHEXParser()
    return parser.parse(text, rule_name=start, filename=filename, **kwargs)


if __name__ == '__main__':
    import json
    from tatsu.util import asjson

    ast = generic_main(main, EHEXParser, name='EHEX')
    print('AST:')
    print(ast)
    print()
    print('JSON:')
    print(json.dumps(asjson(ast), indent=2))
    print()
