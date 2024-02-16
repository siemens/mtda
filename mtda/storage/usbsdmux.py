# ---------------------------------------------------------------------------
# Storage driver for usbsdmux on MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2024 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import subprocess

# Local imports
import mtda.constants as CONSTS
from mtda.storage.helpers.image import Image


class UsbSdMuxStorageController(Image):

    def __init__(self, mtda):
        super().__init__(mtda)
        self.file = "/dev/sda"
        self.control_device = "/dev/sg0"

    """ Configure this storage controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "storage.usbsdmux.configure()")

        result = True
        if 'device' in conf:
            self.file = conf['device']
        if 'control-device' in conf:
            self.control_device = conf['control-device']
        self.mtda.debug(3, f"storage.usbsdmux.configure(): {str(result)}")
        return result

    """ Check presence of the sdmux"""
    def probe(self):
        self.mtda.debug(3, "storage.usbsdmux.probe()")

        result = True
        try:
            subprocess.check_output([
                "usbsdmux", self.control_device, "get"
            ])
        except subprocess.CalledProcessError:
            result = False

        self.mtda.debug(3, f"storage.usbsdmux.probe(): {str(result)}")
        return result

    """ Attach the SD card to the host"""
    def to_host(self):
        self.mtda.debug(3, "storage.usbsdmux.to_host()")

        result = True
        try:
            subprocess.check_output([
                "usbsdmux", self.control_device, "host"
            ])
        except subprocess.CalledProcessError:
            result = False

        self.mtda.debug(3, f"storage.usbsdmux.to_host(): {str(result)}")
        return result

    """ Attach the SD card to the target"""
    def to_target(self):
        self.mtda.debug(3, "storage.usbsdmux.to_target()")
        self.lock.acquire()

        result = self._close()
        if result is True:
            result = self._umount()
        if result is True:
            try:
                subprocess.check_output([
                    "usbsdmux", self.control_device, "dut"
                ])
            except subprocess.CalledProcessError:
                result = False

        self.mtda.debug(3, f"storage.usbsdmux.to_target(): {str(result)}")
        self.lock.release()
        return result

    """ Determine where is the SD card attached"""
    def _status(self):
        self.mtda.debug(3, "storage.usbsdmux.status()")

        try:
            status = subprocess.check_output([
                "usbsdmux", self.control_device, "get"
            ]).decode("utf-8").splitlines()
            result = CONSTS.STORAGE.UNKNOWN
            for s in status:
                if s == "host":
                    result = CONSTS.STORAGE.ON_HOST
                    break
                elif s == "dut":
                    result = CONSTS.STORAGE.ON_TARGET
                    break
        except subprocess.CalledProcessError:
            self.mtda.debug(1, "storage.usbsdmux.status(): usbsdmux failed!")
            result = CONSTS.STORAGE.UNKNOWN

        self.mtda.debug(3, f"storage.usbsdmux.status(): {str(result)}")
        return result


def instantiate(mtda):
    return UsbSdMuxStorageController(mtda)
