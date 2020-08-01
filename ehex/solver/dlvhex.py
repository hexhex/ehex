import shutil
import sys
from subprocess import Popen, PIPE, DEVNULL

from ehex.utils.sys import check_status

DLVHEX = "dlvhex2"


def main(
    *files, src=None, pfilter=None, number=0, debug=False, **options,
):
    executable = shutil.which(DLVHEX)
    if executable is None:
        raise FileNotFoundError(f"could not locate {DLVHEX} executable")

    if pfilter:
        pfilter = ",".join(pfilter)
    if src:
        files = [*files, "--"]

    options.update(filter=pfilter, number=number, silent=True)

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
        for line in proc.stdout:
            yield line

    check_status(proc)
