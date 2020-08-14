import re

from ehex.parser.models import auxmodel
from ehex.parser.models import elpmodel

from ehex.parser.models.auxmodel import PREFIX, NEG_NAME, NAF_NAME
from ehex.utils import model

parse_cache = {}
PAT = re.compile(r'("(?:\\"|[^"])*"|[()])')
SEP = re.compile(r"[{},.]|\s+")


def model_aux_atom(name, args):
    name = model.strip_prefix(name)
    aux_name = name.split("_")[0]

    if aux_name == NEG_NAME:
        # Neg_Guess_M_Naf_Neg_a(...)
        name = name[len(NEG_NAME) + 1 :]
        atom = model_atom(name, args, negation="-")
        return atom

    if aux_name == NAF_NAME:
        # Naf_Neg_a(...)
        name = name[len(NAF_NAME) + 1 :]
        atom = model_atom(name, args)
        return elpmodel.StandardLiteral(negation="not", atom=atom)

    if aux_name == "M" or aux_name == "K":
        # M_Naf_Neg_a(...)
        modality = name[0]
        name = name[2:]
        literal = model_atom(name, args)
        if isinstance(literal, elpmodel.Atom):
            literal = elpmodel.StandardLiteral(atom=literal)
        return elpmodel.ModalLiteral(modality=modality, literal=literal)

    for aux_type in [
        auxmodel.AuxGround,
        auxmodel.AuxGuess,
        auxmodel.AuxMember,
        auxmodel.AuxTrue,
        auxmodel.AuxInput,
        auxmodel.AuxBrave,
        auxmodel.AuxCautious,
    ]:
        if aux_name != aux_type._name:
            continue
        if aux_type.style == "flat":
            # Brave_Neg_a(...)
            name = name[len(aux_type._name) + 1 :]
            atom = model_atom(name, args)
            return aux_type(args=[atom])
        else:
            # Input(...)
            return aux_type(args=args)

    raise ValueError(f'unknown auxiliary name "{name}"')


def model_atom(name, args, negation=None):
    if name.startswith(PREFIX) or name[0].isupper():
        return model_aux_atom(name, args)
    if name.startswith("-"):
        negation = name[0]
        name = name[1:]
    return elpmodel.Atom(negation=negation, name=name, args=args)


def model_term(name, args, negative=False):
    if name.startswith(PREFIX):
        return model_aux_atom(name, args)
    if name.startswith("-"):
        name = name[1:]
        negative = True
    if not args:
        term = name
    else:
        term = elpmodel.FunctionalTerm(name=name, args=args)
    if negative:
        term = elpmodel.NegativeTerm(ast=term)
    return term


def model_args(token):
    if isinstance(token, str):
        return token, ()
    name, args = token
    return name, [model_term(*model_args(a)) for a in args]


def model_token(token):
    try:
        return parse_cache[token]
    except KeyError:
        pass

    atom = model_atom(*model_args(token))
    atom.token = token
    parse_cache[token] = atom
    return atom


def tokenize(text):
    # Adapted from http://stackoverflow.com/a/14715850
    stack = [[]]
    for x in PAT.split(text):
        if x.startswith('"'):
            stack[-1].append(x)
        elif x == "(":
            stack.append([])
        elif x == ")":
            args = tuple(stack.pop())
            if not stack:
                raise ValueError("opening bracket is missing")
            try:
                name = stack[-1][-1]
            except IndexError:
                raise ValueError("expected name before opening bracket")
            stack[-1][-1] = (name, args)
        else:
            stack[-1] += [s for s in SEP.split(x) if s]
    if len(stack) > 1:
        raise ValueError("closing bracket is missing")
    result = [(t, ()) if isinstance(t, str) else t for t in stack.pop()]
    return result


def parse_line(text):
    tokens = tokenize(text)
    return frozenset([model_token(token) for token in tokens])


def parse(stream):
    for line in stream:
        yield parse_line(line)
