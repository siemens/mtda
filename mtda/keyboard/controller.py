import abc


class KeyboardController(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def configure(self, conf):
        """ Configure this keyboard controller from the provided
            configuration"""
        return

    @abc.abstractmethod
    def probe(self):
        """ Check presence of the keyboard controller"""
        return

    @abc.abstractmethod
    def idle(self):
        """ Put the keyboard controller in idle state"""
        return

    @abc.abstractmethod
    def esc(self, repeat=1):
        return False

    @abc.abstractmethod
    def enter(self, repeat=1):
        return False

    @abc.abstractmethod
    def down(self, repeat=1):
        return False

    @abc.abstractmethod
    def left(self, repeat=1):
        return False

    @abc.abstractmethod
    def right(self, repeat=1):
        return False

    @abc.abstractmethod
    def up(self, repeat=1):
        return False

    @abc.abstractmethod
    def write(self, str):
        return
