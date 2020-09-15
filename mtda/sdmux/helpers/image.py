# System imports
import abc
import atexit
import os
import pathlib
import psutil
import subprocess
import threading

# Local imports
from mtda.sdmux.controller import SdMuxController

class Image(SdMuxController):

    def __init__(self, mtda):
        self.mtda   = mtda
        self.handle = None
        self.isloop = False
        self.lock   = threading.Lock()
        atexit.register(self._umount)

    def _close(self):
        self.mtda.debug(3, "sdmux.helpers.image._close()")

        result = True
        if self.handle is not None:
            self.handle.close()
            self.handle = None
            try:
                subprocess.check_output(["sync"])
            except subprocess.CalledProcessError:
                result = False

        self.mtda.debug(3, "sdmux.helpers.image._close(): %s" % str(result))
        return result

    def close(self):
        self.mtda.debug(3, "sdmux.helpers.image.close()")
        self.lock.acquire()

        result = self._close()

        self.mtda.debug(3, "sdmux.helpers.image.close(): %s" % str(result))
        self.lock.release()
        return result

    def _mountpoint(self, path=""):
        result = "/media"
        if os.geteuid() != 0:
            result = os.path.join("/run", "user",str(os.getuid()))
        result = os.path.join(result, "mtda", "sdmux")
        if path:
            result = os.path.join(result, os.path.basename(path))
        return result

    def _umount(self):
        self.mtda.debug(3, "sdmux.helpers.image._umount()")

        result = True
        if self._status() == self.SD_ON_HOST:
            basedir = self._mountpoint()
            if os.path.exists(basedir):
                mounts = [d for d in os.listdir(basedir) if os.path.ismount(os.path.join(basedir, d))]
                for m in mounts:
                    self.mtda.debug(2, "sdmux.helpers.image.umount(): removing mount point for '{0}'".format(m))
                    m = os.path.join(basedir, m)
                    cmd = [ "/bin/umount", m ]
                    if os.geteuid() != 0:
                        cmd.insert(0, "sudo")
                    if os.system(" ".join(cmd)) == 0:
                        os.rmdir(m)
            if self.isloop:
                self.mtda.debug(2, "sdmux.helpers.image.umount(): removing loopback device '{0}'".format(self.device))
                cmd = [ "losetup", "-d", self.device ]
                if os.geteuid() != 0:
                    cmd.insert(0, "sudo")
                if os.system(" ".join(cmd)) == 0:
                    self.device = None
                    self.isloop = False

        self.mtda.debug(3, "sdmux.helpers.image._umount(): %s" % str(result))
        return result

    def umount(self):
        self.mtda.debug(3, "sdmux.helpers.image.umount()")
        self.lock.acquire()

        result = self._umount()

        self.mtda.debug(3, "sdmux.helpers.image.umount(): %s" % str(result))
        self.lock.release()
        return result

    def mount(self, part=None):
        self.mtda.debug(3, "sdmux.helpers.image.mount()")

        result = True
        self.lock.acquire()
        if self._status() == self.SD_ON_HOST:
            self.device = self.file
            p = pathlib.Path(self.file)
            if p.is_block_device() == False:
                cmd = [ "losetup", "-f", "--show", "-P", self.file ]
                if os.geteuid() != 0:
                    cmd.insert(0, "sudo")
                self.isloop = True
                self.device = subprocess.check_output(cmd).decode("utf-8").strip()
                result = self.device != ""
                if result:
                    self.mtda.debug(2, "sdmux.helpers.image.mount(): created loopback device '{0}'".format(self.device))
                else:
                    self.mtda.debug(1, "sdmux.helpers.image.mount(): failed to create loopback for '{0}'".format(self.file))
            if result:
                path = self.device
                if part:
                    tmp = "{0}p{1}".format(self.device, part)
                    if pathlib.Path(tmp).is_block_device():
                        path = tmp
                    else:
                        tmp = "{0}{1}".format(self.device, part)
                        if pathlib.Path(tmp).is_block_device():
                            path = tmp
                        else:
                            result = False
                mountpoint = self._mountpoint(path)
                if os.path.ismount(mountpoint) == False:
                    try:
                        self.mtda.debug(2, "sdmux.helpers.image.mount(): mounting %s on %s" % (path, mountpoint))
                        os.makedirs(mountpoint, exist_ok=True)
                        cmd =["/bin/mount", path, mountpoint]
                        if os.geteuid() != 0:
                            cmd.insert(0, "sudo")
                        subprocess.check_output(cmd)
                    except subprocess.CalledProcessError:
                        self.mtda.debug(1, "sdmux.helpers.image.mount(): mount command failed!")
                        result = False
        else:
            self.mtda.debug(1, "sdmux.helpers.image.mount(): sdmux attached to target!")
            result = False

        self.mtda.debug(3, "sdmux.helpers.image.mount(): %s" % str(result))
        self.lock.release()
        return result

    def open(self):
        self.mtda.debug(3, "sdmux.helpers.image.open()")

        result = True
        self.lock.acquire()
        if self._status() == self.SD_ON_HOST:
            if self.handle is None:
                try:
                    self.handle = open(self.file, "r+b")
                    self.handle.seek(0, 0)
                except:
                    result = False

        self.mtda.debug(3, "sdmux.helpers.image.open(): %s" % str(result))
        self.lock.release()
        return result

    def status(self):
        self.mtda.debug(3, "sdmux.helpers.image.status()")
        self.lock.acquire()

        result = self._status()

        self.mtda.debug(3, "sdmux.helpers.image.status(): %s" % str(result))
        self.lock.release()
        return result

    def supports_hotplug(self):
        return False

    def _locate(self, dst):
        self.mtda.debug(3, "sdmux.helpers.image._locate()")

        result = None
        mountpoint = self._mountpoint(self.device)
        partitions = psutil.disk_partitions()
        for p in partitions:
            if p.mountpoint.startswith(mountpoint):
                path = os.path.join(p.mountpoint, dst)
                if os.path.exists(path):
                    result = path
                    break

        self.mtda.debug(3, "sdmux.helpers.image._locate(): %s" % str(result))
        return result

    def update(self, dst, offset, data):
        self.mtda.debug(3, "sdmux.helpers.image.update()")

        self.lock.acquire()
        f = None
        path = self._locate(dst)
        result = -1
        if path is not None:
            try:
                mode = "ab" if offset > 0 else "wb"
                f = open(path, mode)
                f.seek(offset)
                result = f.write(data)
            finally:
                if f is not None:
                    f.close()

        self.mtda.debug(3, "sdmux.helpers.image.update(): %s" % str(result))
        self.lock.release()
        return result

    def write(self, data):
        self.mtda.debug(3, "sdmux.helpers.image.write()")

        result = False
        self.lock.acquire()
        if self.handle is not None:
            try:
                self.handle.write(data)
                result = True
            except OSError:
                result = False

        self.mtda.debug(3, "sdmux.helpers.image.write(): %s" % str(result))
        self.lock.release()
        return result
