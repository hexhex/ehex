import signal
import sys
from subprocess import Popen, PIPE, DEVNULL

from ehex.utils import check_status


def solve(*files, debug=False, print_errors=None, src="", pfilter=None, **options):
    if print_errors is None:
        print_errors = bool(files)

    options.update({"silent": True, "filter": ",".join(pfilter) if pfilter else None})

    flags = {name for name, value in options.items() if value is True}

    for key in flags:
        del options[key]

    options = {
        key: value
        for key, value in options.items()
        if not (value is None or value is False)
    }

    cmd = ["dlvhex2"]
    cmd.extend("--{}".format(name.replace("_", "-")) for name in flags)
    cmd.extend(
        "--{}={}".format(key.replace("_", "-"), value) for key, value in options.items()
    )
    cmd.extend(files)
    if src:
        cmd.append("--")
    if debug:
        print("{} {}".format(cmd[0], " \\\n  ".join(cmd[1:])), file=sys.stderr)

    proc = Popen(
        cmd,
        stdin=PIPE,
        stdout=PIPE,
        stderr=None if print_errors else DEVNULL,
        universal_newlines=True,
    )

    with proc.stdin as stdin:
        stdin.write(src)

    for line in proc.stdout:
        yield line

    check_status(proc)
