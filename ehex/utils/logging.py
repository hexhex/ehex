import logging


class Message:
    def __init__(self, msg, args):
        self.msg = msg
        self.args = args

    def __str__(self):
        return str(self.msg).format(*self.args)


class EhexLogger(logging.LoggerAdapter):
    def log(self, level, msg, /, *args, **kws):
        if self.isEnabledFor(level):
            msg, kws = self.process(msg, kws)
            self.logger._log(level, Message(msg, args), (), **kws)


def get_logger(name="ehex"):
    return EhexLogger(logging.getLogger(name), extra=None)
