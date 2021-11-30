# ---------------------------------------------------------------------------
# USB Function storage driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2021 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import abc
import os
import subprocess

# Local imports
from mtda.storage.helpers.image import Image


class UsbFunctionController(Image):

    def __init__(self, mtda):
        super().__init__(mtda)
        self.gadget = "usb_functions_for_multi-tenant_device_access"
        self.function = "mass_storage.usb0"
        self.mode = self.SD_ON_HOST
        self.reset = None

    """ Configure this storage controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "storage.usbf.configure()")

        result = None
        if 'gadget' in conf:
            self.gadget = conf['gadget']
        if 'function' in conf:
            self.function = conf['function']
        if 'reset' in conf:
            self.reset = conf['reset']

        self.sysfs = ("/sys/kernel/config/usb_gadget/"
                      "{0}/functions/{1}/lun.0/file").format(
                     self.gadget, self.function)

        self.mtda.debug(3, "storage.usbf.configure(): %s" % str(result))
        return result

    """ Get file used by the USB Function driver"""
    def probe(self):
        self.mtda.debug(3, "storage.usbf.probe()")

        result = True
        try:
            with open(self.sysfs) as conf:
                self.file = conf.read().rstrip()
                conf.close()
        except FileNotFoundError:
            result = False

        self.mtda.debug(3, "storage.usbf.probe(): %s" % str(result))
        return result

    """ Attach the shared storage device to the host"""
    def to_host(self):
        self.mtda.debug(3, "storage.usbf.to_host()")
        self.lock.acquire()

        result = True
        if self.reset:
            os.environ["MASS_STORAGE_FILE"] = ""
            result = (os.system(self.reset)) == 0
        if result:
            self.mode = self.SD_ON_HOST

        self.mtda.debug(3, "storage.usbf.to_host(): %s" % str(result))
        self.lock.release()
        return result

    """ Attach the shared storage device to the target"""
    def to_target(self):
        self.mtda.debug(3, "storage.usbf.to_target()")
        self.lock.acquire()

        result = self._close()
        if result is True:
            result = self._umount()

        if result:
            if self.reset:
                os.environ["MASS_STORAGE_FILE"] = self.file
                result = (os.system(self.reset)) == 0

        if result:
            self.mode = self.SD_ON_TARGET

        self.lock.release()
        self.mtda.debug(3, "storage.usbf.to_target(): %s" % str(result))
        return result

    """ Determine where the shared storage device is attached"""
    def _status(self):
        self.mtda.debug(3, "storage.usbf.status()")

        result = self.mode

        self.mtda.debug(3, "storage.usbf.status(): %s" % str(result))
        return result


def instantiate(mtda):
    return UsbFunctionController(mtda)
