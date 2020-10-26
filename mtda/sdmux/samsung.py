# System imports
import abc
import os
import psutil
import subprocess

# Local imports
from mtda.sdmux.helpers.image import Image


class SamsungSdMuxController(Image):

    def __init__(self, mtda):
        super().__init__(mtda)
        self.device = "/dev/sda"
        self.serial = "sdmux"

    """ Configure this sdmux controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "sdmux.samsung.configure()")

        result = None
        if 'device' in conf:
            self.device = conf['device']
        if 'serial' in conf:
            self.serial = conf['serial']

        self.mtda.debug(3, "sdmux.samsung.configure(): %s" % str(result))
        return result

    """ Check presence of the sdmux controller"""
    def probe(self):
        self.mtda.debug(3, "sdmux.samsung.probe()")

        result = True
        try:
            subprocess.check_output([
                "sd-mux-ctrl", "-e", self.serial, "-i"
            ])
        except subprocess.CalledProcessError:
            result = False

        self.mtda.debug(3, "sdmux.samsung.probe(): %s" % str(result))
        return result

    """ Attach the SD card to the host"""
    def to_host(self):
        self.mtda.debug(3, "sdmux.samsung.to_host()")

        result = True
        try:
            subprocess.check_output([
                "sd-mux-ctrl", "-e", self.serial, "--ts"
            ])
        except subprocess.CalledProcessError:
            result = False

        self.mtda.debug(3, "sdmux.samsung.to_host(): %s" % str(result))
        return result

    """ Attach the SD card to the target"""
    def to_target(self):
        self.mtda.debug(3, "sdmux.samsung.to_target()")
        self.lock.acquire()

        result = self._close()
        if result is True:
            result = self._umount()
        if result is True:
            try:
                subprocess.check_output([
                    "sd-mux-ctrl", "-e", self.serial, "--dut"
                ])
            except subprocess.CalledProcessError:
                result = False

        self.mtda.debug(3, "sdmux.samsung.to_target(): %s" % str(result))
        self.lock.release()
        return result

    """ Determine where is the SD card attached"""
    def _status(self):
        self.mtda.debug(3, "sdmux.samsung.status()")

        try:
            status = subprocess.check_output([
                "sd-mux-ctrl", "-e", self.serial, "-u"
            ]).decode("utf-8").splitlines()
            result = self.SD_ON_UNSURE
            for s in status:
                if s == "SD connected to: TS":
                    result = self.SD_ON_HOST
                    break
                elif s == "SD connected to: DUT":
                    result = self.SD_ON_TARGET
                    break
        except subprocess.CalledProcessError:
            self.mtda.debug(1, "sdmux.samsung.status(): sd-mux-ctrl failed!")
            result = self.SD_ON_UNSURE

        self.mtda.debug(3, "sdmux.samsung.status(): %s" % str(result))
        return result


def instantiate(mtda):
    return SamsungSdMuxController(mtda)
