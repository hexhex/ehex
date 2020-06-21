import sys
import re
from subprocess import Popen, PIPE, DEVNULL

from ehex.utils import check_status


def solve(
    *files,
    mode=None,
    debug=False,
    print_errors=None,
    src="",
    models=None,
    quiet=None,
    **options
):
    if print_errors is None:
        print_errors = bool(files)
    if quiet is None:
        if options.get("enum_mode") in {"brave", "cautious"}:
            quiet = 1
        else:
            quiet = 0

    options.update(
        {
            "verbose": 0,
            "outf": 1,
            "models": 0 if models is None and mode is None else models,
            "quiet": quiet,
            "mode": mode,
        }
    )

    flags = {name for name, value in options.items() if value is True}

    for key in flags:
        del options[key]

    options = {
        key: value
        for key, value in options.items()
        if not (value is None or value is False)
    }

    cmd = ["clingo"]
    cmd.extend("--{}".format(name.replace("_", "-")) for name in flags)
    cmd.extend(
        "--{}={}".format(key.replace("_", "-"), value) for key, value in options.items()
    )
    cmd.extend(files)
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

    if mode == "gringo":
        yield from proc.stdout
        return

    ignore = re.compile(r"^[A-Z%]").match

    for line in proc.stdout:
        if ignore(line):
            continue
        yield line

    check_status(proc)
