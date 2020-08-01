import shutil
import sys
import re
from subprocess import Popen, PIPE, DEVNULL

from ehex.utils.sys import check_status

# https://www.mat.unical.it/aspcomp2013/files/aspoutput.txt
EXIT_CODES = (0, 10, 20, 30, 62)
CLINGO = "clingo"


def main(
    *files, src=None, quiet=None, models=None, debug=False, **options,
):
    executable = shutil.which(CLINGO)
    if executable is None:
        raise FileNotFoundError(f"could not locate {CLINGO} executable")

    if quiet is None:
        if options.get("enum_mode") in {"brave", "cautious"}:
            quiet = 1
        else:
            quiet = 0
    if src:
        files = [*files, "-"]
    mode = options.get("mode")
    if models is None and mode != "gringo":
        models = 0

    options.update(verbose=0, outf=1, quiet=quiet, models=models)

    flags = [
        name.replace("_", "-")
        for name, value in options.items()
        if value is True
    ]
    options = {
        key.replace("_", "-"): value
        for key, value in options.items()
        if value and value is not True or value == 0
    }

    flags = [f"--{name}" for name in flags]
    options = [f"--{key}={value}" for key, value in options.items()]
    args = [executable, *flags, *options, *files]
    if debug:
        cmd = "{} {}".format(executable, " \\\n\t".join(args[1:]))
        print(cmd, file=sys.stderr)
    with Popen(
        args,
        stdin=PIPE,
        stdout=PIPE,
        stderr=None if debug else DEVNULL,
        text=True,
    ) as proc:
        if src:
            with proc.stdin as stdin:
                stdin.write(src)
        if mode == "gringo":
            yield from proc.stdout
        else:
            ignore = re.compile(r"^[A-Z%]").match
            for line in proc.stdout:
                if ignore(line):
                    continue
                yield line

    check_status(proc, expected=EXIT_CODES)
