import re

from ehex import AUX_MARKER, M_PREFIX, K_PREFIX, SNEG_PREFIX, IN_ATOM
from ehex import fragments
from ehex.render import render as render_literal
from ehex.parser.model import KModal, MModal


parse_cache = {}
PAT = re.compile(r'("(?:\\"|[^"])*"|[()])')
SEP = re.compile(r'[{,.}]|\s+')
match_sneg = re.compile(
    r'(-|{}{})_(.+)'.format(AUX_MARKER, SNEG_PREFIX)
).match
match_modal = re.compile(
    '{}({}|{})_({}_)?(.+)'.format(
        AUX_MARKER, K_PREFIX, M_PREFIX, SNEG_PREFIX,
    )
).match


def nested_split(text):
    """Adapted from  http://stackoverflow.com/a/14715850"""
    stack = [[]]
    for x in PAT.split(text):
        if x.startswith('"'):
            stack[-1].append(x)
        elif x == '(':
            symbol = stack[-1][-1]
            terms = []
            stack[-1][-1] = (symbol, terms)
            stack.append(terms)
        elif x == ')':
            stack.pop()
            if not stack:
                raise ValueError('opening bracket is missing')
        else:
            stack[-1] += [s for s in SEP.split(x) if s]
    if len(stack) > 1:
        raise ValueError('closing bracket is missing')
    return stack.pop()


def nkeys(groups):
    return tuple([
        key if isinstance(key, str)
        else nkeys(key)
        for key in groups
    ])


def render(answer_set):
    rendered = [render_literal(lit) for lit in answer_set]
    return '{{{}}}'.format(', '.join(sorted(rendered)))


def generate_tokens(stream):
    for ans in stream:
        yield nested_split(ans)


def _terms(terms):
    return [
        t if isinstance(t, str) else
        fragments.functional_term(t[0], _terms(t[1])) for t in terms
    ]


def _atom(nkey):
    if isinstance(nkey, str):
        return fragments.atom(nkey)
    symbol, terms = nkey
    return fragments.atom(symbol, _terms(terms))


def parsed(tokens):
    aux_in = AUX_MARKER + IN_ATOM
    for nkey in nkeys(tokens):
        try:
            yield parse_cache[nkey]
            continue
        except KeyError:
            pass
        if isinstance(nkey, tuple) and nkey[0].startswith(aux_in):
            value = _atom(nkey[1][0])
            op, sneg, value.symbol = match_modal(value.symbol).groups()
            if sneg:
                value = fragments.neg(value)
            if op == K_PREFIX:
                value = fragments.not_(KModal(literal=value, op='K'))
            else:
                value = MModal(literal=value, op='M')
        else:
            value = _atom(nkey)
            sneg_match = match_sneg(value.symbol)
            if sneg_match:
                value.symbol = sneg_match.group(2)
                value = fragments.neg(value)
        parse_cache[nkey] = value
        yield value


def parse(stream):
    for tokens in generate_tokens(stream):
        yield parsed(tokens)


def render_result(stream):
    for ans in parse(stream):
        yield render(ans)
