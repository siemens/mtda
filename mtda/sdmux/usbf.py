# System imports
import abc
import subprocess

# Local imports
from mtda.sdmux.controller import SdMuxController

class UsbFunctionController(SdMuxController):

    def __init__(self):
        self.gadget   = "usb_functions_for_mentor_test_device_agent"
        self.function = "mass_storage.usb0"
        self.file     = None
        self.handle   = None
        self.mode     = self.SD_ON_HOST

    def close(self):
        if self.handle is not None:
            self.handle.close()
            self.handle = None
            try:
                subprocess.check_output(["sync"])
            except subprocess.CalledProcessError:
                return False
        return True

    def configure(self, conf):
        """ Configure this sdmux controller from the provided configuration"""
        if 'gadget' in conf:
           self.gadget = conf['gadget']
        if 'function' in conf:
           self.function = conf['function']
        return

    def open(self):
        if self.status() != self.SD_ON_HOST:
            return False

        if self.handle is None:
            try:
                self.handle = open(self.file, "r+b")
                return True
            except:
                return False

    def probe(self):
        """ Get file used by the USB Function driver"""
        try:
            with open("/sys/kernel/config/usb_gadget/%s/functions/%s/lun.0/file" % (self.gadget, self.function)) as conf:
                self.file = conf.read().rstrip()
                conf.close()
            return True
        except subprocess.CalledProcessError:
            return False

    def to_host(self):
        """ Attach the SD card to the host"""
        self.mode = self.SD_ON_HOST
        return True

    def to_target(self):
        """ Attach the SD card to the target"""
        try:
            self.close()
            self.mode = self.SD_ON_TARGET
            return True
        except subprocess.CalledProcessError:
            return False

    def status(self):
        """ Determine where is the SD card attached"""
        return self.mode

    def write(self, data):
        if self.handle is None:
            return False
        try:
            self.handle.write(data)
            return True
        except OSError:
            return False

def instantiate():
   return UsbFunctionController()
