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
import atexit
import os
import stat
import subprocess
import pathlib
import time

# Local imports
import mtda.constants as CONSTS
from mtda.storage.helpers.image import Image, MissingCowDeviceError
from mtda.support.usb import Composite
from mtda.utils import SystemdDeviceUnit


# Local constants
DM_BASE = "mtda-base"
DM_COW = "mtda-cow"


class UsbFunctionController(Image):

    def __init__(self, mtda):
        super().__init__(mtda)
        self.user_device = None
        self.user_file = None
        self.base_device = None
        self.cow_device = None
        self.loop_device = None
        self.file = None
        self.mode = CONSTS.STORAGE.ON_HOST
        Composite.mtda = mtda

    def cleanup(self):
        self.mtda.debug(3, "storage.usbf.cleanup()")
        result = None

        self.cleanup_cow()
        if self.loop_device is not None:
            self.mtda.debug(2, "storage.usbf.cleanup(): "
                               f"removing {self.loop_device}")
            cmd = ['/usr/sbin/losetup', '-d', self.loop_device]
            subprocess.check_call(cmd)
            self.loop_device = None

        self.mtda.debug(3, f"storage.usbf.cleanup(): {result}")
        return result

    def cleanup_cow(self):
        if os.path.exists(f"/dev/mapper/{DM_COW}"):
            subprocess.run(['/sbin/kpartx', '-dv', f"/dev/mapper/{DM_COW}"])
            subprocess.run(['/sbin/dmsetup', 'remove', DM_COW])

        if os.path.exists(f"/dev/mapper/{DM_BASE}"):
            subprocess.run(['/sbin/dmsetup', 'remove', DM_BASE])

    """ Configure this storage controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "storage.usbf.configure()")

        result = False
        if 'device' in conf:
            self.user_device = conf['device']
        if 'cow' in conf:
            self.cow_device = conf['cow']
        if 'file' in conf:
            self.user_file = conf['file']
            d = os.path.dirname(self.user_file)
            os.makedirs(d, mode=0o755, exist_ok=True)
            if not os.path.exists(self.user_file):
                sparse = pathlib.Path(self.user_file)
                sparse.touch()
                os.truncate(str(sparse), CONSTS.IMAGE_FILESIZE)

        if self.user_device is None and self.user_file is None:
            raise RuntimeError("shared storage device/file not defined!")

        if self.user_device is not None and self.user_file is not None:
            self.mtda.debug(1, "storage.usbf.configure(): "
                               f"both 'file' ({self.user_file}) and "
                               f"'device' ({self.user_device}) are set, "
                               "using 'file'")
            self.user_device = None

        self.file = self.user_device
        if self.user_file:
            cmd = ['/usr/sbin/losetup', '-f', '--show', self.user_file]
            self.loop_device = subprocess.check_output(cmd, text=True).strip()
            self.file = self.loop_device
            self.mtda.debug(2, "storage.usbf.configure(): created loopback "
                               f"device {self.loop_device} for "
                               f"{self.user_file}")

        self.base_device = None
        if self.cow_device:
            self.configure_cow(conf)

        if self.user_file or self.cow_device:
            atexit.register(self.cleanup)

        self.mtda.debug(3, "storage.usbf.configure(): "
                           f"will use {self.file}")
        conf['_device_'] = self.file
        result = Composite.configure('storage', conf)

        self.mtda.debug(3, f"storage.usbf.configure(): {result}")
        return result

    def configure_cow(self, conf):
        self.base_device = self.file

        self.cleanup_cow()

        cmd = ['/sbin/blockdev', '--getsz', self.base_device]
        self.base_size = subprocess.check_output(cmd, text=True).strip()

        cmd = ['/sbin/dmsetup', 'create', DM_BASE, '--table',
               f"0 {self.base_size} snapshot-origin {self.base_device}"]
        subprocess.check_call(cmd)

        cmd = ['/sbin/dmsetup', 'create', DM_COW, '--table',
               f"0 {self.base_size} snapshot "
               f"{self.base_device} {self.cow_device} P 8"]
        subprocess.check_call(cmd)
        self.file = f"/dev/mapper/{DM_COW}"

    def configure_systemd(self, dir):
        if self.user_device is None or \
           os.path.exists(self.user_device) is False:
            return
        dropin = os.path.join(dir, 'auto-dep-storage.conf')
        SystemdDeviceUnit.create_device_dependency(dropin, self.user_device)

        if self.cow_device is None or os.path.exists(self.cow_device) is False:
            return
        dropin = os.path.join(dir, 'auto-dep-storage-cow.conf')
        SystemdDeviceUnit.create_device_dependency(dropin, self.cow_device)

    def rollback(self, ignore_missing=False):
        if self.cow_device is None:
            if ignore_missing:
                return
            raise MissingCowDeviceError('rollback')

        subprocess.run(['/sbin/kpartx', '-dv', f"/dev/mapper/{DM_COW}"])
        cmd = ['/sbin/dmsetup', 'remove', DM_COW]
        subprocess.check_call(cmd)

        cmd = ['/bin/dd', 'if=/dev/zero', f'of={self.cow_device}',
               'bs=1M', 'count=4', 'conv=fsync']
        subprocess.check_call(cmd)

        cmd = ['/sbin/dmsetup', 'create', DM_COW, '--table',
               f"0 {self.base_size} snapshot "
               f"{self.base_device} {self.cow_device} P 8"]
        subprocess.check_call(cmd)

    def commit(self, ignore_missing=False):
        if self.cow_device is None:
            if ignore_missing:
                return
            raise MissingCowDeviceError('commit')

        # Trigger merge
        cmd = ['/sbin/dmsetup', 'suspend', DM_BASE]
        subprocess.check_call(cmd)

        subprocess.run(['/sbin/kpartx', '-dv', f"/dev/mapper/{DM_COW}"])
        cmd = ['/sbin/dmsetup', 'remove', DM_COW]
        subprocess.check_call(cmd)

        cmd = ['/sbin/dmsetup', 'reload', DM_BASE, '--table',
               f"0 {self.base_size} snapshot-merge "
               f"{self.base_device} {self.cow_device} P 8"]
        subprocess.check_call(cmd)

        cmd = ['/sbin/dmsetup', 'resume', DM_BASE]
        subprocess.check_call(cmd)

        # Wait for merge to complete
        while True:
            cmd = ['/sbin/dmsetup', 'status', DM_BASE]
            status = subprocess.check_output(cmd, text=True).strip()

            if 'snapshort-merge' not in status:
                break

            status = status.split()
            allocated = status[3].split('/')[0]
            metadata = status[4]

            self.mtda.debug(4, "storage.usbf.commit(): "
                               f"allocated={allocated}, metadata={metadata}")
            if allocated == metadata:
                break

            time.sleep(1000)

        # Resume CoW device
        cmd = ['/sbin/dmsetup', 'suspend', DM_BASE]
        subprocess.check_call(cmd)

        cmd = ['/sbin/dmsetup', 'reload', DM_BASE, '--table',
               f"0 {self.base_size} snapshot-origin {self.base_device}"]
        subprocess.check_call(cmd)

        cmd = ['/sbin/dmsetup', 'resume', DM_BASE]
        subprocess.check_call(cmd)

        cmd = ['/sbin/dmsetup', 'create', DM_COW, '--table',
               f"0 {self.base_size} snapshot "
               f"{self.base_device} {self.cow_device} P 8"]
        subprocess.check_call(cmd)

    """ Get file used by the USB Function driver"""
    def probe(self):
        self.mtda.debug(3, "storage.usbf.probe()")

        result = False
        if self.user_device is not None:
            if os.path.exists(self.user_device) is True:
                mode = os.stat(self.user_device).st_mode
                if stat.S_ISBLK(mode) is False:
                    self.mtda.debug(1, "storage.usbf.probe(): "
                                       f"{self.user_device} is not a block "
                                       "device!")

        if self.file is not None:
            if os.path.exists(self.file) is True:
                result = True
            else:
                self.mtda.debug(1, "storage.usbaf.probe(): "
                                   f"{self.file} not found!")
        else:
            self.mtda.debug(1, "storage.usbf.probe(): "
                               "storage device/file not configured!")

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

    def _open(self):
        self.mtda.debug(3, "storage.usbf._open()")

        result = True
        path = None
        if self.cow_device:
            self.rollback()
            path = f"/dev/mapper/{DM_BASE}"
        elif self.loop_device:
            path = self.loop_device
        elif self.user_device:
            path = self.user_device

        self.mtda.debug(3, "storage.usbf._open(): "
                           f"opening {path}")
        self.handle = open(path, "r+b")
        self.handle.seek(0, 0)

        self.mtda.debug(3, f"storage.usbf._open(): {result}")
        return result

    """ Determine where the shared storage device is attached"""
    def _status(self):
        self.mtda.debug(3, "storage.usbf.status()")

        result = self.mode

        self.mtda.debug(3, f"storage.usbf.status(): {result}")
        return result


def instantiate(mtda):
    return UsbFunctionController(mtda)
