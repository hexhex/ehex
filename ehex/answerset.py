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


PAT = re.compile(r'("(?:\\"|[^"])*"|[()])')
SEP = re.compile(r'[{,.}]|\s+')


def nested_split(text):
    """Adapted from  http://stackoverflow.com/a/14715850"""
    stack = [[]]
    for x in PAT.split(text):
        if x.startswith('"'):
            stack[-1].append(x)
        elif x == '(':
            # Nest a new list inside the current list
            current = []
            stack[-1].append(current)
            stack.append(current)
        elif x == ')':
            stack.pop()
            if not stack:
                raise ValueError('opening bracket is missing')
        else:
            stack[-1].extend(s for s in SEP.split(x) if s)
    if len(stack) > 1:
        raise ValueError('closing bracket is missing')
    return stack.pop()


def _flatten(tokens):
    first = True
    for token in tokens:
        if isinstance(token, list):
            yield '('
            yield from _flatten(token)
            yield ')'
        else:
            if first:
                first = False
            else:
                yield ','
            yield token


def parse_literal(token):
    try:
        return parse_cache[token]
    except KeyError:
        literal = _parse(token, rule_name='literal')
        parse_cache[token] = literal
        return literal


def render_literal(literal):
    if isinstance(literal, str):
        return literal
    try:
        return render_cache[literal]
    except KeyError:
        rendered = render_model(literal)
        render_cache[literal] = rendered
        return rendered


def render(answer_set):
    rendered = [render_literal(lit) for lit in answer_set]
    return '{{{}}}'.format(', '.join(sorted(rendered)))


def generate_tokens(stream):
    for ans in stream:
        yield nested_split(ans)


def generate_literals(tokens):
    it = iter(tokens)
    try:
        predicate = next(it)
    except StopIteration:
        return
    for token in it:
        if isinstance(token, list):
            yield ''.join(_flatten((predicate, token)))
            try:
                predicate = next(it)
            except StopIteration:
                return
        else:
            yield predicate
            predicate = token
    yield predicate


def generate_models(literals):
    for literal in literals:
        yield parse_literal(literal)


def parse(stream):
    for tokens in generate_tokens(stream):
        yield generate_models(generate_literals(tokens))


def render_result(stream):
    for parsed in parse(stream):
        yield render(parsed)
