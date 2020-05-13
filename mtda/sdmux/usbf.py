# System imports
import abc
import subprocess

# Local imports
from mtda.sdmux.controller import SdMuxController

class UsbFunctionController(SdMuxController):

    def __init__(self, mtda):
        self.mtda     = mtda
        self.gadget   = "usb_functions_for_mentor_test_device_agent"
        self.function = "mass_storage.usb0"
        self.file     = None
        self.handle   = None
        self.mode     = self.SD_ON_HOST

    def close(self):
        self.mtda.debug(3, "sdmux.usbf.close()")

        result = True
        if self.handle is not None:
            self.handle.close()
            self.handle = None
            try:
                subprocess.check_output(["sync"])
            except subprocess.CalledProcessError:
                result = False

        self.mtda.debug(3, "sdmux.usbf.close(): %s" % str(result))
        return result

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

    def open(self):
        self.mtda.debug(3, "sdmux.usbf.open()")

        result = True
        if self.status() == self.SD_ON_HOST:
            if self.handle is None:
                try:
                    self.handle = open(self.file, "r+b")
                except:
                    result = False
        else:
            self.mtda.debug(1, "sdmux.usbf.open(): storage not attached to host!")
            result = False

        self.mtda.debug(3, "sdmux.usbf.open(): %s" % str(result))
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

        result = self.close()
        if result == True:
            self.mode = self.SD_ON_TARGET

        self.mtda.debug(3, "sdmux.usbf.to_target(): %s" % str(result))
        return result

    """ Determine where is the SD card attached"""
    def status(self):
        self.mtda.debug(3, "sdmux.usbf.status()")

        result = self.mode

        self.mtda.debug(3, "sdmux.usbf.status(): %s" % str(result))
        return result

    def write(self, data):
        self.mtda.debug(3, "sdmux.usbf.write()")

        result = True
        if self.handle is not None:
            try:
                self.handle.write(data)
            except OSError:
                result = False
        else:
            self.mtda.debug(1, "sdmux.usbf.write(): shared storage not opened")
            result = False

        self.mtda.debug(3, "sdmux.usbf.write(): %s" % str(result))
        return result

def instantiate(mtda):
   return UsbFunctionController(mtda)
