import sys

from tatsu.codegen import CodeGenerator, ModelRenderer

from ehex.codegen import elpgen
from ehex.parser.models import auxmodel
from ehex.utils import model
from ehex.utils.decorators import cached

THIS_MODULE = sys.modules[__name__]


class ELPAuxGenerator(CodeGenerator):
    def __init__(self):
        super().__init__(modules=[elpgen, THIS_MODULE])
        self.negations = set()

    def __enter__(self):
        self.negations.clear()
        return self._render

    def __exit__(self, *_):
        self.negations.clear()

    def _render(self, obj):
        value, negations = self._cached_render(obj)
        if negations:
            self.negations.update(negations)
        return value

    @cached
    def _cached_render(self, obj):
        value = self.render(obj)
        return value, self.negations.copy()


class Atom(elpgen.Atom):
    def render_fields(self, fields):
        if fields.get("negation"):
            self.handle_neg(fields)
        return super().render_fields(fields)

    def handle_neg(self, fields):
        if self.node.negation is not model.NO_CONSTRAINT:
            self.context.negations.add((fields["name"], len(fields["args"])))
        fields.update(negation=None, name=model.neg_name(fields["name"]))


class ModalLiteral(ModelRenderer):
    def render_fields(self, fields):
        return self.aux_modal(**fields)

    def aux_modal(self, modality, literal, **_):
        literal = auxmodel.AuxLiteral(
            atom=literal.atom, negation=literal.negation
        )
        literal = model.strip_prefix(self.rend(literal))
        return f"{auxmodel.PREFIX}{modality}_{literal}"


class AuxAtom(Atom):
    def render_fields(self, fields):
        if self.node.style == "flat":
            return self.flat_style(fields)
        fields.setdefault("name", self.node.name)
        return super().render_fields(fields)

    def flat_style(self, fields):
        if fields.get("negation"):
            raise ValueError(
                "flat style auxiliary atoms do not support negation"
            )
        atom = self.rend(fields["args"][0])
        atom = model.strip_prefix(atom)
        return f"{self.node.name}_{atom}"


class AuxLiteral(Atom):
    def render_fields(self, fields):
        return self.aux_literal(**fields)

    def aux_literal(self, negation, atom, **_):
        atom = model.strip_prefix(self.rend(atom))
        if negation:
            return f"{auxmodel.PREFIX}{auxmodel.NAF_NAME}_{atom}"
        return atom


class HEXExternalAtom(ModelRenderer):
    def render_fields(self, fields):
        fields.update(name=self.node.name, program_type=self.node.program_type)
        template = "{name}[{in_args::, :}]"
        if fields["out_args"]:
            template += "({out_args::, :})"
        return template


class HEXReasoningAtom(HEXExternalAtom):
    def render_fields(self, fields):
        query = fields["query"]
        in_args = [
            self.node.program_type,
            fields["program"],
            self.node.input_name,
            model.clone_atom(query, args=[], no_constraint=True),
        ]
        fields.update(
            name=self.node.name, in_args=in_args, out_args=query.args
        )
        return super().render_fields(fields)
