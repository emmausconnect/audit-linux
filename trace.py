import logging

class Tracer:
    __is_initialized: bool = False
    __tracefilename: str = ""
    __logger: logging.Logger = None
    __hdlr: logging.StreamHandler = None
    __loghdlr: logging.StreamHandler = None

    def __init__(self, name: str = "", ts: str = "", debugmode: bool = False):
        if Tracer.__is_initialized:
            return

        Tracer.__logger = logging.getLogger(name)
        Tracer.__logger.setLevel(logging.DEBUG)
        Tracer.__tracefilename = '/tmp/' + '-'.join([f"{name}", "journal", f"{ts}"]).strip('-') + '.txt'

        self.__hdlr = logging.StreamHandler()
        if debugmode:
            self.__hdlr.level = logging.DEBUG
        else:
            self.__hdlr.level = logging.INFO
        formatter = logging.Formatter('[%(levelname)s]: %(message)s')
        self.__hdlr.setFormatter(formatter)

        self.__loghdlr = logging.FileHandler(Tracer.__tracefilename)
        # self.__loghdlr.level = logging.DEBUG
        logformatter = logging.Formatter('[%(levelname)-7s] %(filename)s(%(lineno)d): %(message)s')
        self.__loghdlr.setFormatter(logformatter)

        Tracer.__logger.addHandler(self.__hdlr)  # must be first one added for set_main_level to work properly
        Tracer.__logger.addHandler(self.__loghdlr)

        Tracer.__is_initialized = True


    @classmethod
    def get_tracefilename(cls) -> str:
        return cls.__tracefilename

    @classmethod
    def get_logger(cls) -> logging.Logger:
        return cls.__logger

    @classmethod
    def set_main_level(cls, lvl: int):
        cls.__logger.handlers[0].setLevel(lvl)
        return
