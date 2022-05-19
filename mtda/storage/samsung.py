# ---------------------------------------------------------------------------
# Storage driver for Samsung sdmux on MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import subprocess

# Local imports
import mtda.constants as CONSTS
from mtda.storage.helpers.image import Image


class SamsungSdMuxStorageController(Image):

    def __init__(self, mtda):
        super().__init__(mtda)
        self.file = "/dev/sda"
        self.serial = "sdmux"

    """ Configure this storage controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "storage.samsung.configure()")

        result = None
        if 'device' in conf:
            self.file = conf['device']
        if 'serial' in conf:
            self.serial = conf['serial']

        self.mtda.debug(3, "storage.samsung.configure(): %s" % str(result))
        return result

    """ Check presence of the sdmux"""
    def probe(self):
        self.mtda.debug(3, "storage.samsung.probe()")

        result = True
        try:
            subprocess.check_output([
                "sd-mux-ctrl", "-e", self.serial, "-i"
            ])
        except subprocess.CalledProcessError:
            result = False

        self.mtda.debug(3, "storage.samsung.probe(): %s" % str(result))
        return result

    """ Attach the SD card to the host"""
    def to_host(self):
        self.mtda.debug(3, "storage.samsung.to_host()")

        result = True
        try:
            subprocess.check_output([
                "sd-mux-ctrl", "-e", self.serial, "--ts"
            ])
        except subprocess.CalledProcessError:
            result = False

        self.mtda.debug(3, "storage.samsung.to_host(): %s" % str(result))
        return result

    """ Attach the SD card to the target"""
    def to_target(self):
        self.mtda.debug(3, "storage.samsung.to_target()")
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

        self.mtda.debug(3, "storage.samsung.to_target(): %s" % str(result))
        self.lock.release()
        return result

    """ Determine where is the SD card attached"""
    def _status(self):
        self.mtda.debug(3, "storage.samsung.status()")

        try:
            status = subprocess.check_output([
                "sd-mux-ctrl", "-e", self.serial, "-u"
            ]).decode("utf-8").splitlines()
            result = CONSTS.STORAGE.UNKNOWN
            for s in status:
                if s == "SD connected to: TS":
                    result = CONSTS.STORAGE.ON_HOST
                    break
                elif s == "SD connected to: DUT":
                    result = CONSTS.STORAGE.ON_TARGET
                    break
        except subprocess.CalledProcessError:
            self.mtda.debug(1, "storage.samsung.status(): sd-mux-ctrl failed!")
            result = CONSTS.STORAGE.UNKNOWN

        self.mtda.debug(3, "storage.samsung.status(): %s" % str(result))
        return result


def instantiate(mtda):
    return SamsungSdMuxStorageController(mtda)
