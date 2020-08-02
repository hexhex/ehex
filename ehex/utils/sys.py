import signal
import sys


def check_status(proc, expected=0):
    status = proc.returncode
    if isinstance(expected, int):
        expected = [expected]
    if status not in expected:
        name = proc.args[0]
        if status < 0:
            num = abs(status)
            sig_name = signal.Signals(num).name
            msg = f"{name} was terminated by signal {sig_name}"
            status = 128 + num
        else:
            msg = f"{name} exited with unexpected return code {status}"
        print(msg, file=sys.stderr)
        sys.exit(status)
