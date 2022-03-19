# ---------------------------------------------------------------------------
# USB Function storage driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import os
import stat

# Local imports
from mtda.storage.helpers.image import Image
from mtda.support.usb import Composite


class UsbFunctionController(Image):

    def __init__(self, mtda):
        super().__init__(mtda)
        self.device = None
        self.file = None
        self.mode = self.SD_ON_HOST

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

        if self.file is None and self.device is not None:
            self.file = self.device

        if self.file is not None:
            result = Composite.configure('storage', conf)

        self.mtda.debug(3, "storage.usbf.configure(): {}".format(result))
        return result

    def configure_systemd(self, dir):
        if self.file is None or os.path.exists(self.file) is False:
            return
        mode = os.stat(self.file).st_mode
        if stat.S_ISBLK(mode) is False:
            return
        device = os.path.basename(self.file)
        dropin = os.path.join(dir, 'auto-dep-storage.conf')
        with open(dropin, 'w') as f:
            f.write('[Unit]\n')
            f.write('Wants=dev-{}.device\n'.format(device))
            f.write('After=dev-{}.device\n'.format(device))

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
                result = Composite.install()
            else:
                self.mtda.debug(1, "storage.usbf.probe(): "
                                   "{} not found!".format(self.file))
        else:
            self.mtda.debug(1, "storage.usbf.probe(): "
                               "file not configured!")

        self.mtda.debug(3, "storage.usbf.probe(): {}".format(result))
        return result

    """ Attach the shared storage device to the host"""
    def to_host(self):
        self.mtda.debug(3, "storage.usbf.to_host()")
        self.lock.acquire()

        self.mode = self.SD_ON_HOST
        result = True

        self.mtda.debug(3, "storage.usbf.to_host(): {}".format(result))
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
            self.mode = self.SD_ON_TARGET

        self.lock.release()
        self.mtda.debug(3, "storage.usbf.to_target(): {}".format(result))
        return result

    """ Determine where the shared storage device is attached"""
    def _status(self):
        self.mtda.debug(3, "storage.usbf.status()")

        result = self.mode

        self.mtda.debug(3, "storage.usbf.status(): {}".format(result))
        return result


def instantiate(mtda):
    return UsbFunctionController(mtda)
