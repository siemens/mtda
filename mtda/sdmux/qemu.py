# System imports
import abc
import subprocess

# Local imports
from mtda.sdmux.controller import SdMuxController

class QemuController(SdMuxController):

    def __init__(self, mtda):
        self.mtda     = mtda
        self.file     = "usb.img"
        self.handle   = None
        self.mode     = self.SD_ON_HOST
        self.qemu     = mtda.power_controller

    def close(self):
        self.mtda.debug(3, "sdmux.qemu.close()")

        result = True
        if self.handle is not None:
            self.handle.close()
            self.handle = None
            try:
                subprocess.check_output(["sync"])
            except subprocess.CalledProcessError:
                result = False

        self.mtda.debug(3, "sdmux.qemu.close(): %s" % str(result))
        return result

    """ Configure this sdmux controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "sdmux.qemu.configure()")

        result = None
        if 'file' in conf:
           self.file = conf['file']

        self.mtda.debug(3, "sdmux.qemu.configure(): %s" % str(result))
        return result

    def open(self):
        self.mtda.debug(3, "sdmux.qemu.open()")

        result = True
        if self.status() == self.SD_ON_HOST:
            if self.handle is None:
                try:
                    self.handle = open(self.file, "r+b")
                except:
                    result = False
        else:
            self.mtda.debug(1, "sdmux.qemu.open(): storage not attached to host!")
            result = False

        self.mtda.debug(3, "sdmux.qemu.open(): %s" % str(result))
        return result

    """ Get file used by the USB Function driver"""
    def probe(self):
        self.mtda.debug(3, "sdmux.qemu.probe()")

        result = True
        try:
            output = self.qemu.cmd("usb_add disk:%s" % self.file)
            for line in output.splitlines():
                line = line.strip()
                if "could not add USB device" in line:
                    result = False
                    break
        except:
            result = False

        self.mtda.debug(3, "sdmux.qemu.probe(): %s" % str(result))
        return result

    """ Attach the SD card to the host"""
    def to_host(self):
        self.mtda.debug(3, "sdmux.qemu.to_host()")

        result = True
        self.mode = self.SD_ON_HOST

        self.mtda.debug(3, "sdmux.qemu.to_host(): %s" % str(result))
        return result

    """ Attach the SD card to the target"""
    def to_target(self):
        self.mtda.debug(3, "sdmux.qemu.to_target()")

        result = self.close()
        if result == True:
            self.mode = self.SD_ON_TARGET

        self.mtda.debug(3, "sdmux.qemu.to_target(): %s" % str(result))
        return result

    """ Determine where is the SD card attached"""
    def status(self):
        self.mtda.debug(3, "sdmux.qemu.status()")

        result = self.mode

        self.mtda.debug(3, "sdmux.qemu.status(): %s" % str(result))
        return result

    def write(self, data):
        self.mtda.debug(3, "sdmux.qemu.write()")

        result = True
        if self.handle is not None:
            try:
                self.handle.write(data)
            except OSError:
                result = False
        else:
            self.mtda.debug(1, "sdmux.qemu.write(): shared storage not opened")
            result = False

        self.mtda.debug(3, "sdmux.qemu.write(): %s" % str(result))
        return result

def instantiate(mtda):
   return QemuController(mtda)
