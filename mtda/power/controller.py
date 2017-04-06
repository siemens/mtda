import abc

class PowerController(object):
    __metaclass__ = abc.ABCMeta

    POWERED_OFF = 0
    POWERED_ON  = 1

    @abc.abstractmethod
    def configure(self, conf):
        """ Configure this power controller from the provided configuration"""
        return

    @abc.abstractmethod
    def probe(self):
        """ Check presence of the power controller"""
        return

    @abc.abstractmethod
    def on(self):
        """ Power on the attached device"""
        return

    @abc.abstractmethod
    def off(self):
        """ Power off the attached device"""
        return

    @abc.abstractmethod
    def status(self):
        """ Determine the current power state of the attached device"""
        return POWERED_OFF

    @abc.abstractmethod
    def toggle(self):
        """ Toggle power for the attached device"""
        return

