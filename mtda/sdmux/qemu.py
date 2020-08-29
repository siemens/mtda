# System imports
import abc
import os
import pathlib
import subprocess
import threading

# Local imports
from mtda.sdmux.controller import SdMuxController

class QemuController(SdMuxController):

    def __init__(self, mtda):
        self.mtda     = mtda
        self.file     = "usb-sdmux.img"
        self.handle   = None
        self.id       = None
        self.lock     = threading.Lock()
        self.name     = "sdmux"
        self.mode     = self.SD_ON_HOST
        self.qemu     = mtda.power_controller

    def close(self):
        self.mtda.debug(3, "sdmux.qemu.close()")

        result = True
        self.lock.acquire()
        if self.handle is not None:
            self.handle.close()
            self.handle = None
            try:
                subprocess.check_output(["sync"])
            except subprocess.CalledProcessError:
                result = False

        self.mtda.debug(3, "sdmux.qemu.close(): %s" % str(result))
        self.lock.release()
        return result

    """ Configure this sdmux controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "sdmux.qemu.configure()")

        result = None
        self.lock.acquire()
        if 'file' in conf:
           self.file = os.path.realpath(conf['file'])
           if os.path.exists(self.file) == False:
               sparse = pathlib.Path(self.file)
               sparse.touch()
               os.truncate(str(sparse), 8*1024*1024*1024)
        if 'name' in conf:
            self.name = conf['name']

        self.mtda.debug(3, "sdmux.qemu.configure(): %s" % str(result))
        self.lock.release()
        return result

    def open(self):
        self.mtda.debug(3, "sdmux.qemu.open()")

        result = True
        self.lock.acquire()
        if self.mode == self.SD_ON_HOST:
            if self.handle is None:
                try:
                    self.mtda.debug(2, "sdmux.qemu.open(): opening '%s' on host" % self.file)
                    self.handle = open(self.file, "r+b")
                    self.handle.seek(0, 0)
                except:
                    result = False
        else:
            self.mtda.debug(1, "sdmux.qemu.open(): storage not attached to host!")
            result = False

        self.mtda.debug(3, "sdmux.qemu.open(): %s" % str(result))
        self.lock.release()
        return result

    def add(self):
        self.mtda.debug(3, "sdmux.qemu.add()")

        result = True
        if self.id is None:
            self.id = self.qemu.usb_add(self.name, self.file)
            if self.id is None:
                self.mtda.debug(1, "sdmux.qemu.add(): usb storage could not be added!")
                result = False

        self.mtda.debug(3, "sdmux.qemu.add(): %s" % str(result))
        return result

    def rm(self):
        self.mtda.debug(3, "sdmux.qemu.rm()")

        result = True
        if self.id is not None:
            result = self.qemu.usb_rm(self.name)
            if result == True:
                self.id = None
            else:
                self.mtda.debug(1, "sdmux.qemu.rm(): usb storage could not be removed!")

        self.mtda.debug(3, "sdmux.qemu.rm(): %s" % str(result))
        return result

    """ Get file used by the USB Function driver"""
    def probe(self):
        self.mtda.debug(3, "sdmux.qemu.probe()")

        result = self.qemu.variant == "qemu"
        if result == False:
            self.mtda.debug(1, "sdmux.qemu.probe(): qemu power controller required!")

        self.mtda.debug(3, "sdmux.qemu.probe(): %s" % str(result))
        return result

    def supports_hotplug(self):
        return True

    """ Attach the SD card to the host"""
    def to_host(self):
        self.mtda.debug(3, "sdmux.qemu.to_host()")

        self.lock.acquire()
        result = self.rm()
        if result == True:
            self.mode = self.SD_ON_HOST

        self.mtda.debug(3, "sdmux.qemu.to_host(): %s" % str(result))
        self.lock.release()
        return result

    """ Attach the SD card to the target"""
    def to_target(self):
        self.mtda.debug(3, "sdmux.qemu.to_target()")

        result = self.close()
        self.lock.acquire()
        if result == True:
            result = self.add()
            if result == True:
                self.mode = self.SD_ON_TARGET

        self.mtda.debug(3, "sdmux.qemu.to_target(): %s" % str(result))
        self.lock.release()
        return result

    """ Determine where is the SD card attached"""
    def status(self):
        self.mtda.debug(3, "sdmux.qemu.status()")

        self.lock.acquire()
        result = self.mode

        self.mtda.debug(3, "sdmux.qemu.status(): %s" % str(result))
        self.lock.release()
        return result

    def write(self, data):
        self.mtda.debug(3, "sdmux.qemu.write()")

        result = True
        self.lock.acquire()
        if self.handle is not None:
            try:
                self.handle.write(data)
            except OSError:
                result = False
        else:
            self.mtda.debug(1, "sdmux.qemu.write(): shared storage not opened")
            result = False

        self.mtda.debug(3, "sdmux.qemu.write(): %s" % str(result))
        self.lock.release()
        return result

def instantiate(mtda):
   return QemuController(mtda)
