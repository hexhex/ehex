import re

from ehex.codegen import EHEXCodeGenerator
from ehex.parser.model import EHEXModelBuilderSemantics
from ehex.parser.answerset import HEXAnswerSetParser


render_model = EHEXCodeGenerator().render
render_cache = {}

_parse = HEXAnswerSetParser(
    semantics=EHEXModelBuilderSemantics(),
    parseinfo=False,
).parse
parse_cache = {}


def tokenize_nested(text):
    """Adapted from  http://stackoverflow.com/a/14715850"""
    left = r'[(]'
    right = r'[)]'
    sep = r'"(?:\\"|[^"])*"|[{,.}]|\s+'
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


def render_literal(literal):
    try:
        return render_cache[literal]
    except KeyError:
        rendered = render_model(literal)
        render_cache[literal] = rendered
        return rendered


def render(answer_set):
    rendered = sorted(render_literal(lit) for lit in answer_set)
    return '{' + ', '.join(rendered) + '}'


def generate_tokens(stream):
    for ans in stream:
        yield tokenize_nested(ans)


def generate_literals(tokens):
    it = iter(tokens)
    predicate = next(it)
    for token in it:
        if isinstance(token, list):
            yield flatten([predicate, token])
            predicate = next(it)
        else:
            yield predicate
            predicate = token
    yield predicate


def generate_model(literals):
    for literal in literals:
        yield parse_literal(literal)


def parse(stream):
    for tokens in generate_tokens(stream):
        yield generate_model(generate_literals(tokens))


def render_result(stream):
    for parsed in parse(stream):
        yield render(parsed)
