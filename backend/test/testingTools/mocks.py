from t0wmadatasvcApi.t0wmadatasvcApi import Tier0Api


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
        self.messages = dict()
        self.reset()

    def debug(self, msg):
        if self.level <= self.available_levels["DEBUG"]:
            self.messages["DEBUG"].append(msg)

    def info(self, msg):
        if self.level <= self.available_levels["INFO"]:
            self.messages["INFO"].append(msg)

    def warning(self, msg):
        if self.level <= self.available_levels["WARNING"]:
            self.messages["WARNING"].append(msg)

    def error(self, msg):
        if self.level <= self.available_levels["ERROR"]:
            self.messages["ERROR"].append(msg)

    def reset(self):
        for lvl in self.available_levels:
            self.messages[lvl] = []


class OrderedLoggerMock(LoggerMock):
    def __init__(self, level):
        super(OrderedLoggerMock, self).__init__(level)
        self.msg_number = 1

    def debug(self, msg):
        if self.level <= self.available_levels["DEBUG"]:
            self.messages["DEBUG"].append((self.msg_number, msg))
            self.msg_number += 1

    def info(self, msg):
        if self.level <= self.available_levels["INFO"]:
            self.messages["INFO"].append((self.msg_number, msg))
            self.msg_number += 1

    def warning(self, msg):
        if self.level <= self.available_levels["WARNING"]:
            self.messages["WARNING"].append((self.msg_number, msg))
            self.msg_number += 1

    def error(self, msg):
        if self.level <= self.available_levels["ERROR"]:
            self.messages["ERROR"].append((self.msg_number, msg))
            self.msg_number += 1

    def reset(self):
        super(OrderedLoggerMock, self).reset()
        self.msg_number = 1


class T0ApiStreamAlwaysCompleted(Tier0Api):
    def express_stream_completed(self, run_number):
        return True


class T0ApiStreamNeverCompleted(Tier0Api):
    def express_stream_completed(self, run_number):
        return False
