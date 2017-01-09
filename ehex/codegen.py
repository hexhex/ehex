import sys
from grako.codegen import ModelRenderer
from grako.codegen import CodeGenerator

THIS_MODULE = sys.modules[__name__]


def cautious_getattr(*args):
    val = getattr(*args)
    if val in (0, False):
        return [val]
    return val


class EHEXCodeGenerator(CodeGenerator):
    def __init__(self):
        super(EHEXCodeGenerator, self).__init__(modules=[THIS_MODULE])


class Program(ModelRenderer):

    @property
    def template(self):
        template = '{statements::\\n:%s\n}\n'
        if getattr(self.node, 'query', None) is not None:
            template += '\n{query}\n'
        return template


class Rule(ModelRenderer):

    @property
    def template(self):
        template = '{head}'
        body = getattr(self.node, 'body', [])
        if body:
            if isinstance(body, list) and len(body) <= 1:
                template += ' :- {body::, :}.'
            else:
                template += ' :-\n{body:1:,\n:}.'
        else:
            template += '.'
        return template


class RuleBody(ModelRenderer):

    @property
    def template(self):
        return '{literals::,\n:}'


class Constraint(ModelRenderer):

    template = ':-\n{body:1:,\n:}.'


class WeakConstraint(ModelRenderer):

    template = ':~\n{body:1:,\n:}\n. [{weight_at_level}]'


class Disjunction(ModelRenderer):

    @property
    def template(self):
        # op = getattr(self.node, 'op', 'v')
        op = '|'
        return '{literals:: %s\n:}' % op


class Conjunction(ModelRenderer):

    @property
    def template(self):
        return '{literals::, :}'


class ChoiceRelation(ModelRenderer):

    @property
    def template(self):
        template = '{{{choices::; :%s}}}'
        if getattr(self.node, 'left', None) is not None:
            template = '{left} {left_op} ' + template
        if getattr(self.node, 'right', None) is not None:
            template = template + ' {right_op} {right}'
        return template


class ChoiceElement(ModelRenderer):

    @property
    def template(self):
        template = '{choice}'
        if getattr(self.node, 'literals', []):
            template += ' : {literals::, :}'
        return template


class AggregateRelation(ModelRenderer):

    @property
    def template(self):
        template = '{aggregate}'
        if getattr(self.node, 'left', None) is not None:
            template = '{left} {left_op} ' + template
        if getattr(self.node, 'right', None) is not None:
            template = template + ' {right_op} {right}'
        return template


class AggregateFunction(ModelRenderer):

    template = '{symbol}{{{elements::; :}}}'


class AggregateElement(ModelRenderer):

    @property
    def template(self):
        template = '{terms::, :}'
        if getattr(self.node, 'literals', []):
            template += ' : {literals::, :}'
        return template


class Optimize(ModelRenderer):

    template = '{function}{{{elements::; :}}}.'


class OptimizeElement(ModelRenderer):

    @property
    def template(self):
        template = '{weight_at_level}'
        if getattr(self.node, 'literals', []):
            template += ' : {literals::, :}'
        return template


class Query(ModelRenderer):

    template = '{literal}?'


class Atom(ModelRenderer):

    @property
    def template(self):
        template = '{symbol}'
        if cautious_getattr(self.node, 'arguments', []):
            template += '({arguments::, :})'
        return template


class StrongNegation(ModelRenderer):

    template = '¬{atom}'


class DefaultNegation(ModelRenderer):

    template = 'not {literal}'


class BinaryRelation(ModelRenderer):

    template = '{left} {op} {right}'


class Modal(ModelRenderer):

    template = '{op} {literal}'


class WeighAtLevel(ModelRenderer):

    @property
    def template(self):
        template = '{weight}'
        if getattr(self.node, 'level', None) is not None:
            template += '@{level}'
        if cautious_getattr(self.node, 'terms', []):
            template += ', {terms::, :}'
        return template


class Term(ModelRenderer):

    def render_fields(self, fields):
        fields.update(ast=self.node.ast)

    template = '{ast:: :}'


class SubTerm(Term):

    template = '({ast:: :})'


class NegativeTerm(Term):

    def render_fields(self, fields):
        fields.update(ast=self.node.ast[1:])

    template = '-{ast:: :})'


class FunctionalTerm(ModelRenderer):

    @property
    def template(self):
        template = '{symbol}'
        if cautious_getattr(self.node, 'arguments', []):
            template += '({arguments::, :})'
        return template
