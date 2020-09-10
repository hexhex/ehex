import sys

from tatsu.codegen import CodeGenerator, ModelRenderer

from ehex.codegen import elpgen
from ehex.parser.models.auxmodel import NAF_NAME, PREFIX
from ehex.utils import model

THIS_MODULE = sys.modules[__name__]


class ELPAuxGenerator(CodeGenerator):
    def __init__(self, modules=None):
        if modules is None:
            modules = [elpgen, THIS_MODULE]
        super().__init__(modules=modules)
        self.negations = set()

    def __enter__(self):
        self.negations.clear()
        return self

    def __exit__(self, *_):
        self.negations.clear()


class Atom(elpgen.Atom):
    def render_fields(self, fields):
        if fields.get("negation"):
            self.handle_neg(fields)
        return super().render_fields(fields)

    def handle_neg(self, fields):
        if not fields.get("no_constraint"):
            self.context.negations.add((fields["name"], len(fields["args"])))
        fields.update(negation=None, name=model.neg_name(fields["name"]))


class ModalLiteral(ModelRenderer):
    def render_fields(self, fields):
        return self.aux_modal(**fields)

    def aux_modal(self, modality, literal, **_):
        atom = self.rend(literal.atom)
        atom = model.strip_prefix(atom)
        if literal.negation:
            return f"{PREFIX}{modality}_{NAF_NAME}_{atom}"
        return f"{PREFIX}{modality}_{atom}"


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
