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
