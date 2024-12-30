# ---------------------------------------------------------------------------
# Storage driver for Samsung sdmux on MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
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
        self.serial = None

    """ Configure this storage controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "storage.samsung.configure()")

        result = True
        if 'device' in conf:
            self.file = conf['device']
        if 'serial' in conf:
            self.serial = conf['serial']
        else:
            try:
                self.serial = subprocess.check_output([
                    "sd-mux-ctrl", "--device-id", "0", "--show-serial"
                ])
            except subprocess.CalledProcessError:
                result = False
        self.mtda.debug(2, "storage.samsung."
                           f"configure(): serial: {self.serial}")
        self.mtda.debug(3, f"storage.samsung.configure(): {str(result)}")
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

        self.mtda.debug(3, f"storage.samsung.probe(): {str(result)}")
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

        self.mtda.debug(3, f"storage.samsung.to_host(): {str(result)}")
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

        self.mtda.debug(3, f"storage.samsung.to_target(): {str(result)}")
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

        self.mtda.debug(3, f"storage.samsung.status(): {str(result)}")
        return result


def instantiate(mtda):
    return SamsungSdMuxStorageController(mtda)
