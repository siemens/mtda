# System imports
import abc
import subprocess

# Local imports
from mtda.sdmux.helpers.image import Image

class UsbFunctionController(Image):

    def __init__(self, mtda):
        super().__init__(mtda)
        self.gadget   = "usb_functions_for_mentor_test_device_agent"
        self.function = "mass_storage.usb0"
        self.mode     = self.SD_ON_HOST

    """ Configure this sdmux controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "sdmux.usbf.configure()")

        result = None
        if 'gadget' in conf:
           self.gadget = conf['gadget']
        if 'function' in conf:
           self.function = conf['function']

        self.mtda.debug(3, "sdmux.usbf.configure(): %s" % str(result))
        return result

    """ Get file used by the USB Function driver"""
    def probe(self):
        self.mtda.debug(3, "sdmux.usbf.probe()")

        result = True
        try:
            with open("/sys/kernel/config/usb_gadget/%s/functions/%s/lun.0/file" % (self.gadget, self.function)) as conf:
                self.file = conf.read().rstrip()
                conf.close()
        except:
            result = False

        self.mtda.debug(3, "sdmux.usbf.probe(): %s" % str(result))
        return result

    """ Attach the SD card to the host"""
    def to_host(self):
        self.mtda.debug(3, "sdmux.usbf.to_host()")

        result = True
        self.mode = self.SD_ON_HOST

        self.mtda.debug(3, "sdmux.usbf.to_host(): %s" % str(result))
        return result

    """ Attach the SD card to the target"""
    def to_target(self):
        self.mtda.debug(3, "sdmux.usbf.to_target()")
        self.lock.acquire()

        result = self._close()
        if result == True:
            result = self._umount()

        if result == True:
            self.mode = self.SD_ON_TARGET

        self.lock.release()
        self.mtda.debug(3, "sdmux.usbf.to_target(): %s" % str(result))
        return result

    """ Determine where is the SD card attached"""
    def _status(self):
        self.mtda.debug(3, "sdmux.usbf.status()")

        result = self.mode

        self.mtda.debug(3, "sdmux.usbf.status(): %s" % str(result))
        return result

def instantiate(mtda):
   return UsbFunctionController(mtda)
