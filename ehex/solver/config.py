import hashlib
import logging
import pathlib
import sys
import tempfile
import types
from contextlib import contextmanager


class Config(types.SimpleNamespace):
    debug = False
    elp_in = []
    out_dir = None
    compute_consequences = False
    ground_reduct = False
    planning_mode = False
    guessing_hints = False
    path = types.SimpleNamespace()
    if sys.stdout.isatty():
        log_level = logging.INFO
    else:
        log_level = logging.WARNING
    stdout = sys.stdout
    tmp_dir = None
    sat_check = False

    def setup(self, /, **kws):
        self.__dict__.update(**kws)
        self.setup_paths()
        if self.debug:
            self.stdout = self.path.worlds_out.open("w")
            self.log_level = logging.DEBUG
        return self

    def setup_paths(self):
        path = self.path
        if self.debug or self.out_dir:
            run_dir = "".join(sorted([str(path) for path in self.elp_in]))
            run_dir = hashlib.sha1(run_dir.encode()).hexdigest()[:7]
            run_dir = pathlib.Path(self.out_dir or "out") / run_dir
            run_dir.mkdir(exist_ok=True, parents=True)
        else:
            tmp_dir = tempfile.TemporaryDirectory()
            self.tmp_dir = tmp_dir
            run_dir = pathlib.Path(tmp_dir.name)
        path.run_dir = run_dir

        path.elp_out = run_dir / "parsed.elp"
        path.reduct_out = run_dir / "reduct.lp"
        path.pp_out = run_dir / "positive.lp"
        path.lp_out = run_dir / "level.lp"
        path.opt_consq_out = run_dir / "opt_consq.lp"
        path.opt_reduct_out = run_dir / "opt_reduct.lp"
        if self.debug:
            path.worlds_out = run_dir / "worlds.out"

    def cleanup(self):
        if self.debug:
            self.stdout.close()
        if self.tmp_dir:
            self.tmp_dir.cleanup()
        self.__dict__.clear()


cfg = Config()


@contextmanager
def setup(**kws):
    cfg.setup(**kws)
    try:
        yield cfg
    finally:
        cfg.cleanup()
