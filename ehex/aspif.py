import sys


ASP = "asp"
RULE = "1"
OUTPUT = "4"
END = "0"

DISJUNCTION = 0
CHOICE = 1
NBODY = 0
WBODY = 1


def handle_header(data):
    vm, vn, vr, *tags = data.split()
    return ((vm, vn, vr), tags)


def handle_rule(data):
    h, m, *head = [int(a) for a in data.split()]
    b, n, *body = head[m:]
    if b == WBODY or h == CHOICE:
        raise NotImplementedError
    return ((h, head[:m]), (b, body[:n]))


def handle_output(data):
    m, data = data.split(None, 1)
    m = int(m)
    s = data[:m]
    n, *literals = [int(s) for s in data[m:].split()]
    return (s, literals[:n])


def handle_end():
    return ()


handler = {
    ASP: handle_header,
    RULE: handle_rule,
    OUTPUT: handle_output,
    END: handle_end,
}


def parse(stream):
    for line in stream:
        stmt, *data = line.split(None, 1)
        try:
            handle = handler[stmt]
        except KeyError:
            raise NotImplementedError
        yield stmt, handle(*data)


def _relevant(stream):
    bodies = set()
    symbols = dict()
    facts = set()
    for stype, data in stream:
        if stype == RULE:
            _, (_, body) = data
            bodies.update(abs(b) for b in body)
        if stype == OUTPUT:
            symbol, keys = data
            if keys:
                symbols.update(dict.fromkeys(keys, symbol))
            else:
                facts.add(symbol)
    return (facts, (symbols[key] for key in bodies & symbols.keys()))


def relevant(text, match):
    facts, bodies = _relevant(parse(text))
    facts = [f for f in [match(f) for f in facts] if f]
    bodies = [b for b in [match(b) for b in bodies] if b]
    return facts, bodies


def main():
    for literal in parse(sys.stdin):
        print(literal)


if __name__ == "__main__":
    main()
