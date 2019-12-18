import abc

class SdMuxController(object):
    __metaclass__ = abc.ABCMeta

    SD_ON_UNSURE = "???"
    SD_ON_HOST   = "HOST"
    SD_ON_TARGET = "TARGET"

    @abc.abstractmethod
    def close(self):
        """ Close the SD card device"""
        return False

    @abc.abstractmethod
    def configure(self, conf):
        """ Configure this sdmux controller from the provided configuration"""
        return True

    @abc.abstractmethod
    def mount(self, part):
        """ Mount the SD card device/partition on the host"""
        return False

    @abc.abstractmethod
    def open(self):
        """ Open the SD card device for I/O operations"""
        return False

    @abc.abstractmethod
    def probe(self):
        """ Check presence of the sdmux controller"""
        return False

    @abc.abstractmethod
    def to_host(self):
        """ Attach the SD card to the host"""
        return False

    @abc.abstractmethod
    def to_target(self):
        """ Attach the SD card to the target"""
        return False

    @abc.abstractmethod
    def status(self):
        """ Determine where is the SD card attached"""
        return self.SD_ON_UNSURE

    @abc.abstractmethod
    def write(self, data):
        """ Write data to the device SD card"""
        return False
