from ehex.codegen import EHEXCodeGenerator


_render = EHEXCodeGenerator().render
_cache = {}


def render(fragment):
    if isinstance(fragment, str):
        return fragment
    try:
        return _cache[fragment]
    except KeyError:
        rendered = _render(fragment)
        _cache[fragment] = rendered
        return rendered
