import sys
import hashlib
import pathlib
import tempfile
import types


class Config(types.SimpleNamespace):
    debug = False
    elp_in = []
    out_dir = None
    compute_consequences = False
    ground_reduct = False
    planning_mode = False
    guessing_hints = False

    def setup(self):
        optimizations = [
            self.compute_consequences,
            self.ground_reduct,
            self.planning_mode,
            self.guessing_hints,
        ]
        self.optimize = any(optimizations)
        self.setup_paths()

    def setup_paths(self):
        if self.debug or self.out_dir:
            run_dir = "".join(sorted([str(path) for path in self.elp_in]))
            run_dir = hashlib.sha1(run_dir.encode()).hexdigest()[:7]
            run_dir = pathlib.Path(self.out_dir or "out") / run_dir
            run_dir.mkdir(exist_ok=True, parents=True)
        else:
            self.tmp_dir = tempfile.TemporaryDirectory()
            run_dir = pathlib.Path(self.tmp_dir.name)

        self.reduct_out = run_dir / "reduct.lp"
        self.pp_out = run_dir / "positive.lp"
        self.lp_out = run_dir / "level.lp"
        self.elp_out = run_dir / "parsed.elp"
        if self.debug:
            print(f"Runtime directory: {run_dir}", file=sys.stderr)

    def cleanup(self):
        try:
            self.tmp_dir.cleanup()
        except AttributeError:
            pass
