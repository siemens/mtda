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
import subprocess

# Local imports
import mtda.constants as CONSTS
from mtda.storage.helpers.image import Image, MissingCowDeviceError
from mtda.utils import Size


class QemuController(Image):

    def __init__(self, mtda):
        super().__init__(mtda)
        self.file = "usb-storage.img"
        self.cow = None
        self.id = None
        self.name = "usb-storage"
        self.mode = CONSTS.STORAGE.ON_TARGET
        self.qemu = mtda.power

    """ Configure this storage controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "storage.qemu.configure()")
        self.lock.acquire()

        result = True
        self.size = CONSTS.DEFAULTS.IMAGE_FILESIZE
        if 'file' in conf:
            self.file = os.path.realpath(conf['file'])
        if 'cow' in conf:
            self.cow = os.path.realpath(conf['cow'])
        if 'size' in conf:
            self.size = Size.to_bytes(conf['size'], 'MiB')
        d = os.path.dirname(self.file)
        os.makedirs(d, mode=0o755, exist_ok=True)
        if os.path.exists(self.file) is False:
            subprocess.check_call(['qemu-img', 'create', '-f', 'raw',
                                   self.file, f'{int(self.size / 1024**2)}M'])
        if 'name' in conf:
            self.name = conf['name']

        self.mtda.debug(3, f"storage.qemu.configure(): {str(result)}")
        self.lock.release()
        return result

    def _add(self):
        self.mtda.debug(3, "storage.qemu._add()")

        result = True
        if self.id is None:
            if self.cow and not os.path.exists(self.cow):
                self.rollback()
            self.id = self.qemu.usb_add(
                    self.name,
                    self.cow if self.cow else self.file)
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

    def commit(self, ignore_missing=False):
        if self.cow is None:
            if ignore_missing:
                return
            raise MissingCowDeviceError('commit')

        cmd = ['qemu-img', 'commit', self.cow]
        subprocess.check_call(cmd)

    def rollback(self, ignore_missing=False):
        if self.cow is None:
            if ignore_missing:
                return
            raise MissingCowDeviceError('rollback')

        cmd = ['qemu-img', 'create', '-F', 'raw', '-f', 'qcow2',
               '-b', self.file, self.cow, f'{self.size}M']
        subprocess.check_call(cmd)

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
