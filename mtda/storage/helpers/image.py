# ---------------------------------------------------------------------------
# Helper class for images
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
import pathlib
import psutil
import subprocess
import threading
import io
import hashlib

# Local imports
import mtda.constants as CONSTS
from mtda.storage.controller import StorageController


class BmapWriteError(OSError):
    """
    base-class for all bmap-related errors
    """
    pass


class MissingCowDeviceError(FileNotFoundError):
    """
    A operation on a cow device was requested, but
    none was configured.
    """
    def __init__(self, operation):
        super().__init__(f'{operation} failed: no CoW device was configured!')


class Image(StorageController):
    _is_storage_mounted = False

    def __init__(self, mtda):
        self.mtda = mtda
        self.handle = None
        self.isloop = False
        self.bmapDict = None
        self.crtBlockRange = 0
        self.writtenBytes = 0
        self.mappedBytes = 0
        self.overlap = 0
        self.rangeChkSum = None
        self.lock = threading.Lock()
        atexit.register(self._umount)

    @property
    def is_storage_mounted(self):
        return Image._is_storage_mounted

    def _close(self):
        self.mtda.debug(3, "storage.helpers.image._close()")

        result = True
        if self.handle is not None:
            self.handle.close()
            self.handle = None
            self.bmapDict = None
            if hasattr(self, 'rollback'):
                self.rollback(ignore_missing=True)
            try:
                subprocess.check_output(["sync"])
            except subprocess.CalledProcessError:
                result = False

        self.mtda.debug(3, f"storage.helpers.image._close(): {str(result)}")
        return result

    def close(self):
        self.mtda.debug(3, "storage.helpers.image.close()")

        with self.lock:
            result = self._close()

        self.mtda.debug(3, f"storage.helpers.image.close(): {str(result)}")
        return result

    def _mountpoint(self, path=""):
        result = "/media"
        if os.geteuid() != 0:
            result = os.path.join("/run", "user", str(os.getuid()))
        result = os.path.join(result, "mtda", "storage")
        if path:
            result = os.path.join(result, os.path.basename(path))
        return result

    def _umount(self):
        self.mtda.debug(3, "storage.helpers.image._umount()")

        result = True
        if self._status() == CONSTS.STORAGE.ON_HOST:
            basedir = self._mountpoint()
            if os.path.exists(basedir):
                mounts = [
                    d for d in os.listdir(basedir)
                    if os.path.ismount(os.path.join(basedir, d))]
                mounts.sort()
                mounts.reverse()
                for m in mounts:
                    self.mtda.debug(2, "storage.helpers.image.umount(): "
                                       "removing mount point for '{0}'"
                                       .format(m))
                    m = os.path.join(basedir, m)
                    cmd = ["/bin/umount", m]
                    if os.system(" ".join(cmd)) == 0:
                        os.rmdir(m)
            if self.isloop:
                self.mtda.debug(2, "storage.helpers.image.umount(): "
                                   "removing loopback device '{0}'"
                                   .format(self.device))
                cmd = ["losetup", "-d", self.device]
                if os.system(" ".join(cmd)) == 0:
                    self.device = None
                    self.isloop = False

        self.mtda.debug(3, f"storage.helpers.image._umount(): {str(result)}")
        Image._is_storage_mounted = result is False
        return result

    def umount(self):
        self.mtda.debug(3, "storage.helpers.image.umount()")

        with self.lock:
            result = self._umount()
        self.mtda.debug(3, f"storage.helpers.image.umount(): {str(result)}")
        return result

    def _get_partitions(self):
        self.mtda.debug(3, "storage.helpers.image._get_partitions()")

        self.device = None
        self.isloop = False
        p = pathlib.Path(self.file)
        if p.is_block_device() is True:
            self.device = self.file
            cmd = ['/sbin/kpartx', '-av', self.device]
            subprocess.check_call(cmd)
            result = True
        else:
            cmd = ["losetup", "-f", "--show", "-P", self.file]
            device = subprocess.check_output(cmd).decode("utf-8").strip()
            result = device != ""
            if result:
                self.device = device
                self.isloop = True

        self.mtda.debug(3, "storage.helpers.image."
                           f"_get_partitions(): {str(result)}")
        return result

    def _mount_part(self, path):
        self.mtda.debug(3, "storage.helpers.image._mount_part()")

        cmd = None
        mountpoint = self._mountpoint(path)
        result = False

        if os.path.exists(path) is False:
            self.mtda.debug(1, "storage.helpers.image._mount_part(): "
                               f"{path} does not exist!")
        elif os.path.ismount(mountpoint) is False:
            os.makedirs(mountpoint, exist_ok=True)
            if pathlib.Path(path).is_block_device():
                cmd = ["/bin/mount", path, mountpoint]
            if cmd:
                cmd = " ".join(cmd)
                self.mtda.debug(2, "storage.helpers.image._mount_part(): "
                                   "mounting {0} on {1}"
                                   .format(path, mountpoint))
                self.mtda.debug(2, "storage.helpers.image."
                                   f"_mount_part(): {cmd}")
                result = (os.system(cmd)) == 0

            if result is False:
                os.rmdir(mountpoint)
        else:
            self.mtda.debug(1, "storage.helpers.image._mount_part(): "
                               "{0} is a mount point".format(mountpoint))

        self.mtda.debug(3, "storage.helpers.image."
                           f"_mount_part(): {str(result)}")
        return result

    def _part_dev(self, path, part):
        if path[-1:].isdigit():
            return f"{path}p{part}"
        else:
            return f"{path}{part}"

    def mount(self, part=None):
        self.mtda.debug(3, "storage.helpers.image.mount()")
        with self.lock:
            result = self._mount_impl(part)
        if result is True:
            Image._is_storage_mounted = True
        self.mtda.debug(3, "storage.helpers.image."
                           f"mount(): {str(result)}")
        return result

    def _mount_impl(self, part=None):
        result = True
        if self._status() == CONSTS.STORAGE.ON_HOST:
            result = self._get_partitions()
            if result:
                self.mtda.debug(2, "storage.helpers.image.mount(): "
                                   "'{0}' holds partitions"
                                   .format(self.device))
            else:
                self.mtda.debug(1, "storage.helpers.image.mount(): "
                                   "failed to get partitions for '{0}'"
                                   .format(self.file))
            if result:
                path = None
                if part:
                    path = self._part_dev(self.device, part)
                else:
                    path = self.device
                if path:
                    result = self._mount_part(path)
        else:
            self.mtda.debug(1, "storage.helpers.image.mount(): "
                               "storage attached to target!")
            result = False

        return result

    def open(self):
        self.mtda.debug(3, "storage.helpers.image.open()")
        with self.lock:
            result = True
            if self._status() == CONSTS.STORAGE.ON_HOST:
                if self.handle is None:
                    result = self._open()
        self.mtda.debug(3, f"storage.helpers.image.open(): {str(result)}")
        return result

    def _open(self):
        self.handle = open(self.file, "r+b")
        self.handle.seek(0, 0)
        return True

    def path(self):
        self.mtda.debug(3, "storage.helpers.image.path()")
        result = self.file
        self.mtda.debug(3, f"storage.helpers.image.open(): {result}")
        return result

    def status(self):
        self.mtda.debug(3, "storage.helpers.image.status()")
        with self.lock:
            result = self._status()

        self.mtda.debug(3, f"storage.helpers.image.status(): {str(result)}")
        return result

    def _get_hasher_by_name(self):
        algo = self.bmapDict["ChecksumType"]
        if algo == 'sha256':
            return hashlib.sha256()
        elif algo == 'md5':
            return hashlib.md5()
        else:
            self.mtda.debug(1, "storage.helpers.image._get_hasher_by_name(): "
                               "unknown hash algorithm %s" % algo)
            return None

    def setBmap(self, bmapDict):
        self.bmapDict = bmapDict
        self.crtBlockRange = 0
        self.writtenBytes = 0
        self.mappedBytes = 0
        self.overlap = 0
        if bmapDict is not None:
            blocksize = bmapDict["BlockSize"]
            # bytes missing in the last block until it is full
            last_block_missing = -bmapDict["ImageSize"] % blocksize
            self.rangeChkSum = self._get_hasher_by_name()
            # the last block is not full, if the imagesize is not a multiple of the blocksize
            self.mappedBytes = bmapDict["MappedBlocksCount"] * blocksize - last_block_missing

    def supports_hotplug(self):
        return False

    def _locate(self, dst):
        self.mtda.debug(3, "storage.helpers.image._locate()")

        result = None
        mountpoint = self._mountpoint(self.device)
        partitions = psutil.disk_partitions()
        for p in partitions:
            if p.mountpoint.startswith(mountpoint):
                path = os.path.join(p.mountpoint, dst)
                if os.path.exists(path):
                    result = path
                    break

        self.mtda.debug(3, f"storage.helpers.image._locate(): {str(result)}")
        return result

    def update(self, dst):
        self.mtda.debug(3, "storage.helpers.image.update()")

        with self.lock:
            if self.handle is None:
                path = self._locate(dst)
                self.handle = open(path, "wb")
            else:
                raise RuntimeError("already opened")
            self.mtda.debug(3, "storage.helpers.image.update(): exit")

    def write(self, data):
        self.mtda.debug(3, "storage.helpers.image.write()")

        with self.lock:
            result = None
            if self.handle is not None:
                # Check if there is a valid bmapDict, write all data otherwise
                if self.bmapDict is not None:
                    result = self._write_with_bmap(data)
                else:
                    # No bmap
                    result = self.handle.write(data)
                    self.mtda.notify_write(size=len(data))

        self.mtda.debug(3, f"storage.helpers.image.write(): {str(result)}")
        return result

    def _write_with_bmap(self, data):
        cur_range = self.bmapDict["BlockMap"][self.crtBlockRange]
        blksize = self.bmapDict["BlockSize"]
        imageBytes = self.bmapDict["ImageSize"]
        # offset within the data buffer
        offset = 0
        # remaining bytes in data buffer
        remaining = len(data) - offset
        while remaining:
            writtenBlocks = self.writtenBytes // blksize
            if writtenBlocks > cur_range["last"]:
                self.crtBlockRange += 1
                cur_range = self.bmapDict["BlockMap"][self.crtBlockRange]

            if writtenBlocks >= cur_range["first"]:
                # bmap ranges are inclusive. Exclusive ranges like [from, to)
                # are easier to handle, hence add one block
                cur_last_block = cur_range["last"] + 1
                end = min(remaining, (cur_last_block - writtenBlocks) * blksize - self.overlap)
                nbytes = self._write_with_chksum(data[offset:offset + end])
                # either we completed our range, or we are at the end of the image
                if self.writtenBytes + nbytes in [cur_last_block * blksize, imageBytes]:
                    self._validate_and_reset_range()
                self.mtda.notify_write(size=nbytes, mapped=self.mappedBytes)
            else:
                # the range already got incremented, hence we need to iterate
                # until the begin of the current range
                nbytes = min(remaining,
                             (cur_range["first"] - writtenBlocks)
                             * blksize - self.overlap)
                self.handle.seek(nbytes, io.SEEK_CUR)
                self.mtda.notify_write(seek=nbytes, mapped=self.mappedBytes)
            self.writtenBytes += nbytes
            self.overlap = self.writtenBytes % blksize
            offset += nbytes
            remaining -= nbytes

        return offset

    def _validate_and_reset_range(self):
        if not self.rangeChkSum:
            return
        cur_range = self.bmapDict["BlockMap"][self.crtBlockRange]
        first = cur_range['first']
        last = cur_range['last']
        obs_chksum = self.rangeChkSum.hexdigest()
        exp_chksum = cur_range['chksum']
        self.mtda.debug(2, "storage.helpers.image._validate_and_reset_range(): "
                           f"checksum of range {first}:{last} is {obs_chksum}")
        if exp_chksum == obs_chksum:
            self.rangeChkSum = self._get_hasher_by_name()
            return
        raise BmapWriteError(
            "checksum mismatch for blocks range %d-%d: "
            "calculated %s, should be %s"
            % (first, last, obs_chksum, exp_chksum))

    def _write_with_chksum(self, data):
        if self.rangeChkSum:
            self.rangeChkSum.update(data)
        result = self.handle.write(data)
        return result
