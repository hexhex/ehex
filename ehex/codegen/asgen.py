import sys

from tatsu.codegen import ModelRenderer
from tatsu.codegen import CodeGenerator

from ehex.codegen import elpgen

THIS_MODULE = sys.modules[__name__]


class AnswerSetGenerator(CodeGenerator):
    def __init__(self):
        super().__init__(modules=[elpgen, THIS_MODULE])


class Atom(elpgen.Atom):
    def render_fields(self, fields):
        if fields.get("negation"):
            fields["negation"] = "¬"
        return super().render_fields(fields)


class AnswerSet(ModelRenderer):
    def render_fields(self, fields):
        elements = [self.rend(e) for e in fields["elements"]]
        elements.sort()
        fields.update(elements=elements)

    template = "{{{elements::, :}}}\n"
