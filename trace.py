import logging

class Tracer:
    __is_initialized: bool = False
    __tracefilename: str = ""
    __logger: logging.Logger = None

    def __init__(self, name: str = "", ts: str = ""):
        if Tracer.__is_initialized:
            return

        Tracer.__logger = logging.getLogger(name)
        Tracer.__tracefilename = '/tmp/' + '-'.join([f"{name}", "journal", f"{ts}"]).strip('-') + '.txt'

        self.hdlr = logging.StreamHandler()
        self.hdlr.level = logging.INFO
        formatter = logging.Formatter('[%(levelname)s]: %(message)s')
        self.hdlr.setFormatter(formatter)

        self.loghdlr = logging.FileHandler(Tracer.__tracefilename)
        self.loghdlr.level = logging.DEBUG
        logformatter = logging.Formatter('[%(levelname)-7s] %(filename)s(%(lineno)d): %(message)s')
        self.loghdlr.setFormatter(logformatter)

        Tracer.__logger.addHandler(self.hdlr)
        Tracer.__logger.addHandler(self.loghdlr)

        Tracer.__is_initialized = True


    @classmethod
    def get_tracefilename(cls) -> str:
        return cls.__tracefilename

    @classmethod
    def get_logger(cls) -> logging.Logger:
        return cls.__logger
