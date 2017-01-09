import re

from ehex.codegen import EHEXCodeGenerator
from ehex.parser.model import EHEXModelBuilderSemantics
from ehex.parser.answerset import HEXAnswerSetParser


render = EHEXCodeGenerator().render
render_cache = {}

_parse = HEXAnswerSetParser(
    semantics=EHEXModelBuilderSemantics(),
    parseinfo=False,
).parse
parse_cache = {}


def get_nested_tokens(text):
    """Adapted from  http://stackoverflow.com/a/14715850"""
    left = r'[(]'
    right = r'[)]'
    sep = r'"(?:\\"|[^"])*"|[{,}]|\s+'
    pat = re.compile(r'({}|{}|{})'.format(left, right, sep))
    tokens = pat.split(text)
    left = re.compile(left).match
    right = re.compile(right).match
    sep = re.compile(sep).match
    stack = [[]]
    for x in tokens:
        if x and x.startswith('"'):
            stack[-1].append(x)
            continue
        if not x or sep(x):
            continue
        if left(x):
            # Nest a new list inside the current list
            current = []
            stack[-1].append(current)
            stack.append(current)
        elif right(x):
            stack.pop()
            if not stack:
                raise ValueError('opening bracket is missing')
        else:
            stack[-1].append(x)
    if len(stack) > 1:
        raise ValueError('closing bracket is missing')
    return stack.pop()


def flatten(tokens):
    tokens = [
        '(' + flatten(token) + ')'
        if isinstance(token, list) else ',' + token
        for token in tokens
    ]
    return ''.join(tokens)[1:]


def generate_tokens(stream):
    for ans in stream:
        if not ans.strip():
            continue
        yield get_nested_tokens(ans)


def parse_literal(token):
    cached = parse_cache.get(token)
    if cached is not None:
        return cached
    literal = _parse(token, rule_name='literal')
    parse_cache[token] = literal
    parse_cache[literal] = token
    return literal


def unparse_literal(literal):
    return parse_cache[literal]


def generate_model(tokens):
    it = iter(tokens)
    predicate = next(it)
    for token in it:
        if isinstance(token, list):
            parts = '{}({})'.format(predicate, flatten(token))
            yield parse_literal(parts)
            predicate = next(it)
        else:
            yield parse_literal(predicate)
            predicate = token
    yield parse_literal(predicate)


def parse(stream):
    for result in generate_tokens(stream):
        yield generate_model(result)


def render_literal(literal):
    cached = render_cache.get(literal)
    if cached is not None:
        return cached
    rendered = render(literal)
    render_cache[literal] = rendered
    return rendered


def render_answer_set(answer_set):
    rendered = sorted(render_literal(lit) for lit in answer_set)
    return '{' + ', '.join(rendered) + '}'


def render_result(stream):
    for parsed in parse(stream):
        yield render_answer_set(parsed)
