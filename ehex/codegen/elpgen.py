import sys

from tatsu.codegen import ModelRenderer
from tatsu.codegen import CodeGenerator

THIS_MODULE = sys.modules[__name__]


class ELPGenerator(CodeGenerator):
    def __init__(self):
        super().__init__(modules=[THIS_MODULE])


# ELP Modal Literals


class ModalLiteral(ModelRenderer):
    def render_fields(self, fields):
        template = "{modality} {literal}"
        if fields.get("negation"):
            template = "{negation} " + template
        return template


# ASP Program


class Program(ModelRenderer):
    template = "{rules::\n\n:}\n"


class Rule(ModelRenderer):
    def render_fields(self, fields):
        if len(fields["body"]) < 2:
            template = ":- {body::, :}."
        else:
            template = ":- \n{body:1:,\n:}."
        if fields["head"]:
            if fields["body"]:
                template = "{head} " + template
            else:
                template = "{head}."
        return template


class Disjunction(ModelRenderer):
    def render_fields(self, fields):
        return "{atoms:: |\n:}"


# ASP Literals


class StandardLiteral(ModelRenderer):
    def render_fields(self, fields):
        template = "{atom}"
        if fields.get("negation"):
            template = "{negation} " + template
        return template


class Atom(ModelRenderer):
    def render_fields(self, fields):
        template = "{name}"
        fields.setdefault("name", self.node.name)
        if fields.get("negation"):
            template = fields["negation"] + template
        if fields["args"]:
            template += "({args::, :})"
        return template


class BuiltinAtom(ModelRenderer):
    template = "{left} {rel} {right}"


class ChoiceAtom(ModelRenderer):
    def render_fields(self, fields):
        template = "{{{elements::; :}}}"
        if fields["left"]:
            template = "{left} {left_rel} " + template
        if fields["right"]:
            template += " {right_rel} {right}"
        return template


class ChoiceElement(ModelRenderer):
    def render_fields(self, fields):
        template = "{atom}"
        if fields["literals"]:
            template += ": {literals::, :}"
        return template


class AggregateLiteral(StandardLiteral):
    pass


class AggregateAtom(ModelRenderer):
    def render_fields(self, fields):
        elements = [e for e in fields["elements"] if e.terms or e.literals]
        fields.update(elements=elements)

        template = "{name}{{{elements::; :}}}"
        if fields.get("left_rel"):
            template = "{left} {left_rel} " + template
        if fields.get("right_rel"):
            template += " {right_rel} {right}"
        return template


class AggregateElement(ModelRenderer):
    def render_fields(self, fields):
        template = "{terms::, :}"
        if fields["literals"]:
            template += " : {literals::, :}"
        return template


# ASP Terms


class Term(ModelRenderer):
    def render_fields(self, fields):
        fields.setdefault("value", self.node.ast)

    template = "{value}"


class IntervalTerm(Term):
    template = "{value::..:}"


class ArithmeticTerm(Term):
    template = "{value:: :}"


class FunctionalTerm(ModelRenderer):
    template = "{name}({args::, :})"


class NegativeTerm(Term):
    template = "-{value}"


class SubTerm(Term):
    template = "({value})"
