# ---------------------------------------------------------------------------
# USB Function storage driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import os
import stat
import subprocess

# Local imports
import mtda.constants as CONSTS
from mtda.storage.helpers.image import Image
from mtda.support.usb import Composite
from mtda.utils import SystemdDeviceUnit


class UsbFunctionController(Image):

    def __init__(self, mtda):
        super().__init__(mtda)
        self.device = None
        self.file = None
        self.loop = None
        self.mode = CONSTS.STORAGE.ON_HOST
        Composite.mtda = mtda

    def cleanup(self):
        self.mtda.debug(3, "storage.usbf.cleanup()")

        result = None
        if self.loop is not None:
            self.mtda.debug(2, f"storage.usbf.cleanup(): removing {self.loop}")
            cmd = ['/usr/sbin/losetup', '-d', self.loop]
            self.loop = subprocess.check_call(cmd)

        self.mtda.debug(3, f"storage.usbf.cleanup(): {result}")
        return result

    """ Configure this storage controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "storage.usbf.configure()")

        result = False
        if 'device' in conf:
            self.device = conf['device']
        if 'file' in conf:
            self.file = conf['file']

        if self.device is not None and self.file is not None:
            self.mtda.debug(1, "storage.usbf.configure(): "
                               "both 'file' ({}) and 'device' ({}) are set, "
                               "using 'file'".format(self.file, self.device))
            self.device = None
        elif self.device is None:
            import atexit
            cmd = ['/usr/sbin/losetup', '-f', '--show', self.file]
            self.loop = subprocess.check_output(cmd).decode("utf-8").strip()
            atexit.register(self.cleanup)
            self.mtda.debug(2, "storage.usbf.configure(): created loopback "
                               "device {} for {}".format(self.loop, self.file))
        else:
            self.file = self.device

        if self.file is not None:
            result = Composite.configure('storage', conf)

        self.mtda.debug(3, f"storage.usbf.configure(): {result}")
        return result

    def configure_systemd(self, dir):
        if self.file is None or os.path.exists(self.file) is False:
            return
        mode = os.stat(self.file).st_mode
        if stat.S_ISBLK(mode) is False:
            return
        dropin = os.path.join(dir, 'auto-dep-storage.conf')
        SystemdDeviceUnit.create_device_dependency(dropin, self.file)

    """ Get file used by the USB Function driver"""
    def probe(self):
        self.mtda.debug(3, "storage.usbf.probe()")

        result = False
        if self.device is not None:
            if os.path.exists(self.device) is True:
                mode = os.stat(self.device).st_mode
                if stat.S_ISBLK(mode) is False:
                    self.mtda.debug(1, "storage.usbf.probe(): "
                                       "{} is not a block "
                                       "device!".format(self.device))
        if self.file is not None:
            if os.path.exists(self.file) is True:
                result = True
            else:
                self.mtda.debug(1, "storage.usbf."
                                   f"probe(): {self.file} not found!")
        else:
            self.mtda.debug(1, "storage.usbf.probe(): "
                               "file not configured!")

        self.mtda.debug(3, f"storage.usbf.probe(): {result}")
        return result

    """ Attach the shared storage device to the host"""
    def to_host(self):
        self.mtda.debug(3, "storage.usbf.to_host()")
        self.lock.acquire()

        self.mode = CONSTS.STORAGE.ON_HOST
        result = True

        self.mtda.debug(3, f"storage.usbf.to_host(): {result}")
        self.lock.release()
        return result

    """ Attach the shared storage device to the target"""
    def to_target(self):
        self.mtda.debug(3, "storage.usbf.to_target()")
        self.lock.acquire()

        result = self._close()
        if result is True:
            result = self._umount()

        if result is True:
            self.mode = CONSTS.STORAGE.ON_TARGET

        self.lock.release()
        self.mtda.debug(3, f"storage.usbf.to_target(): {result}")
        return result

    """ Determine where the shared storage device is attached"""
    def _status(self):
        self.mtda.debug(3, "storage.usbf.status()")

        result = self.mode

        self.mtda.debug(3, f"storage.usbf.status(): {result}")
        return result


def instantiate(mtda):
    return UsbFunctionController(mtda)
