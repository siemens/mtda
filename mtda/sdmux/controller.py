import abc

class SdMuxController(object):
    __metaclass__ = abc.ABCMeta

    SD_ON_UNSURE = 0
    SD_ON_HOST   = 1
    SD_ON_TARGET = 2

    @abc.abstractmethod
    def configure(self, conf):
        """ Configure this sdmux controller from the provided configuration"""
        return

    @abc.abstractmethod
    def probe(self):
        """ Check presence of the sdmux controller"""
        return False

    @abc.abstractmethod
    def to_host(self):
        """ Attach the SD card to the host"""
        return

    @abc.abstractmethod
    def to_target(self):
        """ Attach the SD card to the target"""
        return

    @abc.abstractmethod
    def status(self):
        """ Determine where is the SD card attached"""
        return self.SD_ON_UNSURE
