class LoggerMock(object):
    def __init__(self, level):
        self.available_levels = {
            "DEBUG": 1,
            "INFO": 2,
            "WARNING": 3,
            "ERROR": 4
        }
        if level not in self.available_levels:
            raise ValueError('Invalid logging level')
        self.level = self.available_levels[level]

    def debug(self, msg):
        if self.level <= self.available_levels["DEBUG"]:
            print msg

    def info(self, msg):
        if self.level <= self.available_levels["INFO"]:
            print msg

    def warning(self, msg):
        if self.level <= self.available_levels["WARNING"]:
            print msg

    def error(self, msg):
        if self.level <= self.available_levels["ERROR"]:
            print msg

class T0ApiMock(object):
    def method(self):
        pass