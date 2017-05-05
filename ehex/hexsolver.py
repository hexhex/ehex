from subprocess import (
    Popen,
    PIPE,
    DEVNULL
)


def solve(*args, text='', pfilter=None):
    cmd = ['dlvhex2', '--silent']
    if pfilter is not None:
        cmd += ['--filter=' + ','.join(pfilter or [])]
    cmd += args
    if text:
        cmd.append('--')
    if args:
        print('{} {} \\\n  '.format(*cmd[:2]) +
              ' \\\n  '.join(cmd[2:]))
    proc = Popen(
        cmd,
        stdin=PIPE,
        stdout=PIPE,
        stderr=None if args else DEVNULL,
        universal_newlines=True,
    )
    with proc.stdin as stdin:
        stdin.write(text)
        for name in args:
            with open(name) as src:
                text = src.read()
                stdin.write(text)
    for line in proc.stdout:
        yield line
