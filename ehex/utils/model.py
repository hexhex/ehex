from ehex.parser.models import auxmodel
from ehex.parser.models import elpmodel


def opposite(node):
    if isinstance(node, elpmodel.Atom):
        negation = None if node.negation else "-"
        return type(node)(negation=negation, args=node.args)
    if isinstance(node, elpmodel.StandardLiteral):
        negation = None if node.negation else "not"
        return type(node)(negation=negation, atom=node.atom)
    if isinstance(node, elpmodel.ModalLiteral):
        modality = "K" if node.modality == "M" else "M"
        literal = opposite(node.literal)
        return type(node)(modality=modality, literal=literal)
    raise ValueError(f"opposite of type {type(node)} is undefined")


def weak_form(modal):
    if modal.modality == "K":
        # Strong modal to weak modal: K a -> M not a, K not a -> M a
        return opposite(modal)
    return modal


def clone_atom(atom, model=None, name=None, **kws):
    kws.setdefault("negation", atom.negation)
    kws.setdefault("args", atom.args[:])
    model = model or type(atom)
    if not issubclass(model, auxmodel.AuxAtom):
        kws["name"] = name or atom.name
    return model(**kws)


def clone_literal(obj, **kws):
    if isinstance(obj, elpmodel.ModalLiteral):
        kws.setdefault("modality", obj.modality)
        kws.setdefault("negation", obj.negation)
        kws.setdefault("literal", clone_literal(obj.literal))
        return type(obj)(**kws)
    if isinstance(obj, elpmodel.StandardLiteral):
        kws.setdefault("negation", obj.negation)
        kws.setdefault("atom", clone_atom(obj.atom))
        return type(obj)(**kws)
    raise ValueError(f"cloning literal of type {type(obj)} is undefined")


def strip_prefix(name):
    pfx = auxmodel.PREFIX
    if name.startswith(pfx):
        name = name[len(pfx) :]
    return name


def neg_name(name):
    pfx = auxmodel.PREFIX
    neg = auxmodel.NEG_NAME
    name = strip_prefix(name)
    return f"{pfx}{neg}_{name}"


def key(obj):
    if isinstance(obj, elpmodel.ModalLiteral):
        return (obj.negation, obj.modality, key(obj.literal))
    if isinstance(obj, elpmodel.StandardLiteral):
        return (obj.negation, key(obj.atom))
    if isinstance(obj, elpmodel.Atom):
        return (obj.negation, obj.name, len(obj.args))
    if isinstance(obj, dict):
        return (obj["name"], len(obj["args"]))
    raise ValueError(f"key for object of type {type(obj)} is undefined")
