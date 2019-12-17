import abc

class ConsoleInterface(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def configure(self, conf):
        """ Configure this console from the provided configuration"""
        return

    @abc.abstractmethod
    def probe(self):
        """ Check presence of the console"""
        return

    @abc.abstractmethod
    def close(self):
        """ Close the console interface"""
        return

    @abc.abstractmethod
    def pending(self):
        """ Return number of pending bytes to read"""
        return 0

    @abc.abstractmethod
    def read(self, n=1):
        """ Read from the console"""
        return 0

    @abc.abstractmethod
    def write(self, data):
        """ Write to the console"""
        return 0

