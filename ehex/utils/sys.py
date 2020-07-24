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
            msg = "{} was terminated by signal {}"
            msg.format(name, signal.Signals(num).name)
            status = 128 + num
        else:
            msg = "{} exited with unexpected return code {}"
            msg = msg.format(name, status)
        print(msg, file=sys.stderr)
        sys.exit(status)
