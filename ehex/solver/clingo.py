import re
import shutil
from subprocess import DEVNULL, PIPE, Popen

from ehex.solver.config import cfg
from ehex.utils import logging
from ehex.utils.sys import check_status

# https://www.mat.unical.it/aspcomp2013/files/aspoutput.txt
EXIT_CODES = (0, 10, 20, 30, 62)
SOLVER = "clingo"
logger = logging.get_logger(__name__)


def main(*files, src="", quiet=None, models=None, **options):
    executable = shutil.which(SOLVER)
    if executable is None:
        raise FileNotFoundError(f"could not locate {SOLVER} executable")

    if quiet is None:
        if options.get("enum_mode") in {"brave", "cautious"}:
            quiet = 1
        else:
            quiet = 0
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
        if value and value is not True or value == 0 and value is not False
    }

    flags = [f"--{name}" for name in flags]
    options = [f"--{key}={value}" for key, value in options.items()]
    args = [executable, *flags, *options, *files, "-"]
    if cfg.debug:
        logger.debug("solving...\n{} {}", executable, " \\\n\t".join(args[1:]))

    with Popen(
        args,
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE if cfg.debug else DEVNULL,
        text=True,
    ) as proc:
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
        if cfg.debug:
            msg = proc.stderr.read().rstrip()
            if msg:
                logger.debug("{}.stderr:\n{}", SOLVER, msg)

    check_status(proc, expected=EXIT_CODES)
