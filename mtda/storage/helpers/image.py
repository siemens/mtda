# ---------------------------------------------------------------------------
# Helper class for images
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2023 Siemens Digital Industries Software
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

# Local imports
import mtda.constants as CONSTS
from mtda.storage.controller import StorageController


class Image(StorageController):

    def __init__(self, mtda):
        self.mtda = mtda
        self.handle = None
        self.isfuse = False
        self.isloop = False
        self.bmapDict = None
        self.lastBlockIdx = 0
        self.crtBlockRange = 0
        self.overlap = 0
        self.lock = threading.Lock()
        atexit.register(self._umount)

    def _close(self):
        self.mtda.debug(3, "storage.helpers.image._close()")

        result = True
        if self.handle is not None:
            self.handle.close()
            self.handle = None
            try:
                subprocess.check_output(["sync"])
            except subprocess.CalledProcessError:
                result = False

        self.mtda.debug(3, "storage.helpers.image._close(): %s" % str(result))
        return result

    def close(self):
        self.mtda.debug(3, "storage.helpers.image.close()")
        self.lock.acquire()

        result = self._close()

        self.mtda.debug(3, "storage.helpers.image.close(): %s" % str(result))
        self.lock.release()
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
                    if os.geteuid() != 0:
                        cmd.insert(0, "sudo")
                    if os.system(" ".join(cmd)) == 0:
                        os.rmdir(m)
            if self.isfuse:
                device = self.device[:-1]
                self.mtda.debug(2, "storage.helpers.image.umount(): "
                                   "removing FUSE mount '{0}'".format(device))
                cmd = ["/bin/umount", device]
                if os.system(" ".join(cmd)) == 0:
                    os.rmdir(device)
                    self.device = None
                    self.isfuse = False
            elif self.isloop:
                self.mtda.debug(2, "storage.helpers.image.umount(): "
                                   "removing loopback device '{0}'"
                                   .format(self.device))
                cmd = ["losetup", "-d", self.device]
                if os.geteuid() != 0:
                    cmd.insert(0, "sudo")
                if os.system(" ".join(cmd)) == 0:
                    self.device = None
                    self.isloop = False

        self.mtda.debug(3, "storage.helpers.image._umount(): %s" % str(result))
        return result

    def umount(self):
        self.mtda.debug(3, "storage.helpers.image.umount()")
        self.lock.acquire()

        result = self._umount()

        self.mtda.debug(3, "storage.helpers.image.umount(): %s" % str(result))
        self.lock.release()
        return result

    def _get_partitions(self):
        self.mtda.debug(3, "storage.helpers.image._get_partitions()")

        self.device = None
        self.isfuse = False
        self.isloop = False
        p = pathlib.Path(self.file)
        if self.mtda.fuse is True and os.path.exists("/usr/bin/partitionfs"):
            device = os.path.join(
                "/run", "user", str(os.getuid()), "mtda", "storage", "0")
            os.makedirs(device, exist_ok=True)
            cmd = "/usr/bin/partitionfs -s {0} {1}".format(self.file, device)
            self.mtda.debug(2, "storage.helpers.image._get_partitions(): "
                               "{0}".format(cmd))
            result = (os.system(cmd)) == 0
            if result:
                self.device = device + "/"
                self.isfuse = True
        elif p.is_block_device() is True:
            self.device = self.file
            result = True
        else:
            cmd = ["losetup", "-f", "--show", "-P", self.file]
            if os.geteuid() != 0:
                cmd.insert(0, "sudo")
            device = subprocess.check_output(cmd).decode("utf-8").strip()
            result = device != ""
            if result:
                self.device = device
                self.isloop = True

        self.mtda.debug(3, "storage.helpers.image._get_partitions(): "
                           "%s" % str(result))
        return result

    def _mount_part(self, path):
        self.mtda.debug(3, "storage.helpers.image._mount_part()")

        cmd = None
        mountpoint = self._mountpoint(path)
        result = False

        if os.path.exists(path) is False:
            self.mtda.debug(1, "storage.helpers.image._mount_part(): "
                               "{0} does not exist!".format(path))
        elif os.path.ismount(mountpoint) is False:
            os.makedirs(mountpoint, exist_ok=True)
            if pathlib.Path(path).is_block_device():
                cmd = ["/bin/mount", path, mountpoint]
                if os.geteuid() != 0:
                    cmd.insert(0, "sudo")
            elif self.isfuse:
                cmd = None
                fstype = subprocess.check_output(["/usr/bin/file", path])
                fstype = fstype.decode("utf-8").strip()
                if 'ext4 filesystem' in fstype:
                    cmd = ["/usr/bin/fusext2", path, mountpoint, "-o", "rw+"]
                elif 'FAT (32 bit)' in fstype:
                    cmd = ["/usr/bin/fusefat", path, mountpoint]
                else:
                    self.mtda.debug(1, "storage.helpers.image._mount_part(): "
                                       "{0}".format(fstype))
                    self.mtda.debug(1, "storage.helpers.image._mount_part(): "
                                       "file-system not supported")
            if cmd:
                cmd = " ".join(cmd)
                self.mtda.debug(2, "storage.helpers.image._mount_part(): "
                                   "mounting {0} on {1}"
                                   .format(path, mountpoint))
                self.mtda.debug(2, "storage.helpers.image._mount_part(): "
                                   "{0}".format(cmd))
                result = (os.system(cmd)) == 0

            if result is False:
                os.rmdir(mountpoint)
        else:
            self.mtda.debug(1, "storage.helpers.image._mount_part(): "
                               "{0} is a mount point".format(mountpoint))

        self.mtda.debug(3, "storage.helpers.image._mount_part(): "
                           "%s" % str(result))
        return result

    def _part_dev(self, path, part):
        if path[-1:].isdigit():
            return "{0}p{1}".format(path, part)
        else:
            return "{0}{1}".format(path, part)

    def mount(self, part=None):
        self.mtda.debug(3, "storage.helpers.image.mount()")
        self.lock.acquire()

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

        self.mtda.debug(3, "storage.helpers.image.mount(): %s" % str(result))
        self.lock.release()
        return result

    def open(self):
        self.mtda.debug(3, "storage.helpers.image.open()")
        self.lock.acquire()

        result = True
        if self._status() == CONSTS.STORAGE.ON_HOST:
            if self.handle is None:
                try:
                    self.handle = open(self.file, "r+b")
                    self.handle.seek(0, 0)
                except FileNotFoundError:
                    result = False

        self.mtda.debug(3, "storage.helpers.image.open(): %s" % str(result))
        self.lock.release()
        return result

    def status(self):
        self.mtda.debug(3, "storage.helpers.image.status()")
        self.lock.acquire()

        result = self._status()

        self.mtda.debug(3, "storage.helpers.image.status(): %s" % str(result))
        self.lock.release()
        return result

    def setBmap(self, bmapDict):
        self.bmapDict = bmapDict
        self.crtBlockRange = 0
        self.lastBlockIdx = 0
        self.overlap = 0

    def supports_hotplug(self):
        return False

    def tell(self):
        self.mtda.debug(3, "storage.helpers.image.tell()")
        self.lock.acquire()

        result = None
        if self.handle is not None:
            result = self.handle.tell()

        self.mtda.debug(3, "storage.helpers.image.tell(): %s" % str(result))
        self.lock.release()
        return result

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

        self.mtda.debug(3, "storage.helpers.image._locate(): %s" % str(result))
        return result

    def update(self, dst, offset):
        self.mtda.debug(3, "storage.helpers.image.update()")

        with self.lock:
            result = False
            if self.handle is None:
                path = self._locate(dst)
                if path is not None:
                    mode = "ab" if offset > 0 else "wb"
                    self.handle = open(path, mode)
                    self.handle.seek(offset)
                    result = True
                else:
                    self.mtda.debug(1, "storage.helpers.image.update(): "
                                       "%s could not be found!" % str(dst))
                    raise FileNotFoundError(dst + " could not be found!")
            else:
                self.mtda.debug(1, "storage.helpers.image.update(): "
                                   "shared storage already opened!")

            self.mtda.debug(3, "storage.helpers.image.update(): "
                               "%s" % str(result))
            return result

    def write(self, data):
        self.mtda.debug(3, "storage.helpers.image.write()")
        self.lock.acquire()

        result = None
        if self.handle is not None:
            # Check if there is a valid bmapDict, write all data otherwise
            if self.bmapDict is not None:
                result = 0
                datalen = len(data)
                blksz = self.bmapDict["BlockSize"]
                cRange = self.bmapDict["BlockMap"][self.crtBlockRange]
                # This happens at xz,bz2 and gz compression
                # since the decompressed chunk can be smaller than a block
                if datalen < blksz:
                    # If there is overlap and the new data is enough
                    # to form a block, write it
                    if self.overlap + datalen >= blksz:
                        dataBlockWritten = \
                            self.handle.write(data[0:(blksz-self.overlap)])
                        result += dataBlockWritten
                        self.lastBlockIdx += 1
                        # Write the rest of the data
                        rest = self.handle.write(data[dataBlockWritten:])
                        result += rest
                        self.overlap = rest
                        self.mtda.debug(3, "storage.helpers.image.write(): %s"
                                        % str(result))
                        self.lock.release()
                        return result
                    else:
                        # Not enough data to even write a block
                        # write it and add to the overlap
                        subBlockWritten = self.handle.write(data)
                        result += subBlockWritten
                        self.overlap += subBlockWritten
                        self.mtda.debug(3, "storage.helpers.image.write(): %s"
                                        % str(result))
                        self.lock.release()
                        return result
                # Complete partially written last block,
                # start blockpointer depending on this
                if self.overlap:
                    result += self.handle.write(data[0:(blksz-self.overlap)])
                    self.lastBlockIdx += 1
                    b = blksz-self.overlap
                else:
                    b = 0

                while b < datalen:
                    if self.lastBlockIdx > cRange['last']:
                        self.crtBlockRange += 1
                        cRange = \
                            self.bmapDict["BlockMap"][self.crtBlockRange]
                    flBlks2Write = 1
                    advanceBlocks = 1
                    if self.lastBlockIdx >= cRange['first']:
                        flBlks2Write = int((datalen-b)/blksz)
                        # Write multiple blocks if possible in that range
                        if (self.lastBlockIdx + flBlks2Write) < cRange['last']:
                            # Check if it is a full Block
                            if flBlks2Write:
                                result += self.handle.write(
                                    data[b:b+flBlks2Write*blksz])
                                advanceBlocks = flBlks2Write
                            else:
                                result += self.handle.write(data[b:b+blksz])
                                # Needed for incrementing dynamic blockpointer
                                flBlks2Write = 1
                        else:
                            result += self.handle.write(data[b:b+blksz])
                            flBlks2Write = 1
                    else:
                        # If there is a block to skip use the opportunity
                        # to also drop the overlap, skip the subBlock
                        # This allows for faster write-times
                        # since the time consuming self.handle.write()
                        # does not need to be called at the start
                        # when there is no overlap anymore
                        if self.overlap:
                            b += self.overlap
                            self.handle.seek(self.overlap, io.SEEK_CUR)
                            self.overlap = 0
                        self.handle.seek(min(datalen-b, blksz), io.SEEK_CUR)
                    # Only increment block index in case we wrote full blocks
                    if b + blksz*flBlks2Write <= datalen:
                        self.lastBlockIdx += advanceBlocks
                    else:
                        self.overlap = datalen - b
                    # Increase blockpointer
                    b += flBlks2Write * blksz
            else:
                # No bmap
                result = self.handle.write(data)
        self.mtda.debug(3, "storage.helpers.image.write(): %s" % str(result))
        self.lock.release()
        return result
