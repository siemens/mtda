# ---------------------------------------------------------------------------
# QEMU storage driver for MTDA
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
import pathlib

# Local imports
import mtda.constants as CONSTS
from mtda.storage.helpers.image import Image


class QemuController(Image):

    def __init__(self, mtda):
        super().__init__(mtda)
        self.file = "usb-storage.img"
        self.id = None
        self.name = "usb-storage"
        self.mode = CONSTS.STORAGE.ON_TARGET
        self.qemu = mtda.power

    """ Configure this storage controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "storage.qemu.configure()")
        self.lock.acquire()

        result = True
        if 'file' in conf:
            self.file = os.path.realpath(conf['file'])
        d = os.path.dirname(self.file)
        os.makedirs(d, mode=0o755, exist_ok=True)
        if os.path.exists(self.file) is False:
            sparse = pathlib.Path(self.file)
            sparse.touch()
            os.truncate(str(sparse), CONSTS.IMAGE_FILESIZE)
        if 'name' in conf:
            self.name = conf['name']

        self.mtda.debug(3, f"storage.qemu.configure(): {str(result)}")
        self.lock.release()
        return result

    def _add(self):
        self.mtda.debug(3, "storage.qemu._add()")

        result = True
        if self.id is None:
            self.id = self.qemu.usb_add(self.name, self.file)
            if self.id is None:
                self.mtda.debug(1, "storage.qemu._add(): "
                                   "usb storage could not be added!")
                result = False

        self.mtda.debug(3, f"storage.qemu._add(): {str(result)}")
        return result

    def _rm(self):
        self.mtda.debug(3, "storage.qemu._rm()")

        result = True
        if self.id is not None:
            result = self.qemu.usb_rm(self.name)
            if result is True:
                self.id = None
            else:
                self.mtda.debug(1, "storage.qemu._rm(): "
                                   "usb storage could not be removed!")

        self.mtda.debug(3, f"storage.qemu._rm(): {str(result)}")
        return result

    """ Get file used by the USB Function driver"""
    def probe(self):
        self.mtda.debug(3, "storage.qemu.probe()")
        self.lock.acquire()

        result = self.qemu.variant == "qemu"
        if result is False:
            self.mtda.debug(1, "storage.qemu.probe(): "
                               "qemu power controller required!")

        self.mtda.debug(3, f"storage.qemu.probe(): {str(result)}")
        self.lock.release()
        return result

    def supports_hotplug(self):
        return True

    """ Attach the shared storage device to the host"""
    def to_host(self):
        self.mtda.debug(3, "storage.qemu.to_host()")
        self.lock.acquire()

        result = self._rm()
        if result is True:
            self.mode = CONSTS.STORAGE.ON_HOST

        self.mtda.debug(3, f"storage.qemu.to_host(): {str(result)}")
        self.lock.release()
        return result

    """ Attach the shared storage device to the target"""
    def to_target(self):
        self.mtda.debug(3, "storage.qemu.to_target()")
        self.lock.acquire()

        result = self._close()
        if result is True:
            result = self._umount()
        if result is True:
            result = self._add()
            if result is True:
                self.mode = CONSTS.STORAGE.ON_TARGET

        self.mtda.debug(3, f"storage.qemu.to_target(): {str(result)}")
        self.lock.release()
        return result

    """ Determine where the shared storage device is attached"""
    def _status(self):
        self.mtda.debug(3, "storage.qemu.status()")

        result = self.mode

        self.mtda.debug(3, f"storage.qemu.status(): {str(result)}")
        return result


def instantiate(mtda):
    return QemuController(mtda)
