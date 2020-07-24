import sys

from tatsu.codegen import ModelRenderer
from tatsu.codegen import CodeGenerator

from ehex.utils import model
from ehex.codegen import elpgen
from ehex.parser.models import elpmodel
from ehex.parser.models.auxmodel import PREFIX, NAF_NAME

THIS_MODULE = sys.modules[__name__]


class ELPAuxGenerator(CodeGenerator):
    def __init__(self, modules=None):
        if modules is None:
            modules = [elpgen, THIS_MODULE]
        super().__init__(modules=modules)
        self.aux_neg_keys = set()
        self.aux_rules = []


class Program(elpgen.Program):
    def __init__(self, *args, **kws):
        super().__init__(*args, **kws)
        self.context.aux_neg_keys.clear()
        self.context.aux_rules.clear()

    def render_fields(self, fields):
        rules = [self.rend(rule) for rule in fields["rules"]]
        fields.update(rules=rules + self.context.aux_rules)


class Atom(elpgen.Atom):
    def render_fields(self, fields):
        if fields.get("negation"):
            self.handle_neg(fields)
        return super().render_fields(fields)

    def handle_neg(self, fields):
        name = fields["name"]
        args = fields["args"]
        if not fields.get("no_constraint"):
            key = (name, len(args))
            if key not in self.context.aux_neg_keys:
                self.context.aux_neg_keys.add(key)
                self.context.aux_rules.append(self.aux_neg_rule(*key))
        fields.update(negation=None, name=model.neg_name(name))

    @staticmethod
    def aux_neg_rule(name, arity):
        args = [f"T{i+1}" for i in range(arity)]
        atom = elpmodel.Atom(name=name, args=args)
        natom = model.clone_atom(atom, negation="-")
        return elpmodel.Rule(head=None, body=[atom, natom])


class ModalLiteral(ModelRenderer):
    def render_fields(self, fields):
        return self.aux_modal(**fields)

    def aux_modal(self, modality, literal, **kws):
        atom = self.rend(literal.atom)
        model.strip_prefix(atom)
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
        q = fields["query"]
        in_args = [
            self.node.program_type,
            fields["program"],
            self.node.input_name,
            model.clone_atom(q, args=[], no_constraint=True),
        ]
        fields.update(name=self.node.name, in_args=in_args, out_args=q.args)
        return super().render_fields(fields)
