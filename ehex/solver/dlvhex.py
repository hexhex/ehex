import shutil
from subprocess import DEVNULL, PIPE, Popen

from ehex.solver.config import cfg
from ehex.utils import logging
from ehex.utils.sys import check_status

SOLVER = "dlvhex2"
logger = logging.get_logger(__name__)


def main(
    *files, src=None, pfilter=None, number=0, **options,
):
    executable = shutil.which(SOLVER)
    if executable is None:
        raise FileNotFoundError(f"could not locate {SOLVER} executable")

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
        if value and value is not True or value == 0 and value is not False
    }

    flags = [f"--{name}" for name in flags]
    options = [f"--{key}={value}" for key, value in options.items()]
    args = [executable, *flags, *options, *files]
    if cfg.debug:
        logger.debug("{} {}", executable, " \\\n\t".join(args[1:]))

    with Popen(
        args,
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE if cfg.debug else DEVNULL,
        text=True,
    ) as proc:
        if src:
            with proc.stdin as stdin:
                stdin.write(src)
        for line in proc.stdout:
            yield line
        if cfg.debug:
            msg = proc.stderr.read().rstrip()
            if msg:
                logger.debug("{}.stderr:\n{}", SOLVER, msg)

    check_status(proc)
