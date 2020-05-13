# System imports
import abc
import os
import psutil
import subprocess

# Local imports
from mtda.sdmux.controller import SdMuxController

class SamsungSdMuxController(SdMuxController):

    def __init__(self, mtda):
        self.mtda   = mtda
        self.device = "/dev/sda"
        self.handle = None
        self.serial = "sdmux"

    def close(self):
        self.mtda.debug(3, "sdmux.samsung.close()")

        result = True
        if self.handle is not None:
            self.handle.close()
            self.handle = None
            try:
                subprocess.check_output(["sync"])
            except subprocess.CalledProcessError:
                result = False

        self.mtda.debug(3, "sdmux.samsung.close(): %s" % str(result))
        return result

    """ Configure this sdmux controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "sdmux.samsung.configure()")

        result = None
        if 'device' in conf:
           self.device = conf['device']
        if 'serial' in conf:
           self.serial = conf['serial']

        self.mtda.debug(3, "sdmux.samsung.configure(): %s" % str(result))
        return result

    def mount(self, part=None):
        self.mtda.debug(3, "sdmux.samsung.mount()")

        result = True
        if self.status() == self.SD_ON_HOST:
            path = self.device
            if part:
                path = path + part
            mountpoint = os.path.join("/media", "mtda", os.path.basename(path))
            if os.path.ismount(mountpoint) == False:
                try:
                    os.makedirs(mountpoint, exist_ok=True)
                    subprocess.check_call(["/bin/mount", path, mountpoint])
                except subprocess.CalledProcessError:
                    self.mtda.debug(1, "sdmux.samsung.mount(): mount command failed!")
                    result = False
        else:
            self.mtda.debug(1, "sdmux.samsung.mount(): sdmux attached to target!")
            result = False

        self.mtda.debug(3, "sdmux.samsung.mount(): %s" % str(result))
        return result

    def open(self):
        self.mtda.debug(3, "sdmux.samsung.open()")

        result = True
        if self.status() == self.SD_ON_HOST:
            if self.handle is None:
                try:
                    self.handle = open(self.device, "r+b")
                except:
                    result = False

        self.mtda.debug(3, "sdmux.samsung.open(): %s" % str(result))
        return result

    """ Check presence of the sdmux controller"""
    def probe(self):
        self.mtda.debug(3, "sdmux.samsung.probe()")

        result = True
        try:
            subprocess.check_output([
                "sd-mux-ctrl", "-e", self.serial, "-t"
            ])
        except subprocess.CalledProcessError:
            result = False

        self.mtda.debug(3, "sdmux.samsung.probe(): %s" % str(result))
        return result

    """ Attach the SD card to the host"""
    def to_host(self):
        self.mtda.debug(3, "sdmux.samsung.to_host()")

        result = True
        try:
            subprocess.check_output([
                "sd-mux-ctrl", "-e", self.serial, "--ts"
            ])
        except subprocess.CalledProcessError:
            result = False

        self.mtda.debug(3, "sdmux.samsung.to_host(): %s" % str(result))
        return result

    """ Attach the SD card to the target"""
    def to_target(self):
        self.mtda.debug(3, "sdmux.samsung.to_target()")

        result = True
        try:
            mountpoint = os.path.join("/media", "mtda", os.path.basename(self.device))
            partitions = psutil.disk_partitions()
            for p in partitions:
                if p.mountpoint.startswith(mountpoint):
                    subprocess.check_call(["/bin/umount", p.mountpoint])
            self.close()
            subprocess.check_output([
                "sd-mux-ctrl", "-e", self.serial, "--dut"
            ])
        except subprocess.CalledProcessError:
            result = False

        self.mtda.debug(3, "sdmux.samsung.to_target(): %s" % str(result))
        return result

    """ Determine where is the SD card attached"""
    def status(self):
        self.mtda.debug(3, "sdmux.samsung.status()")

        try:
            status = subprocess.check_output([
                "sd-mux-ctrl", "-e", self.serial, "-u"
            ]).decode("utf-8").splitlines()
            result = self.SD_ON_UNSURE
            for s in status:
                if s == "SD connected to: TS":
                    result = self.SD_ON_HOST
                    break
                elif s == "SD connected to: DUT":
                    result = self.SD_ON_TARGET
                    break
        except subprocess.CalledProcessError:
            self.mtda.debug(1, "sdmux.samsung.status(): sd-mux-ctrl failed!")
            result = self.SD_ON_UNSURE

        self.mtda.debug(3, "sdmux.samsung.status(): %s" % str(result))
        return result

    def _locate(self, dst):
        self.mtda.debug(3, "sdmux.samsung._locate()")

        result = None
        mountpoint = os.path.join("/media", "mtda", os.path.basename(self.device))
        partitions = psutil.disk_partitions()
        for p in partitions:
            if p.mountpoint.startswith(mountpoint):
                path = os.path.join(p.mountpoint, dst)
                if os.path.exists(path):
                    result = path
                    break

        self.mtda.debug(3, "sdmux.samsung._locate(): %s" % str(result))
        return result

    def update(self, dst, offset, data):
        self.mtda.debug(3, "sdmux.samsung.update()")

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

        self.mtda.debug(3, "sdmux.samsung.update(): %s" % str(result))
        return result

    def write(self, data):
        self.mtda.debug(3, "sdmux.samsung.write()")

        result = False
        if self.handle is not None:
            try:
                self.handle.write(data)
                result = True
            except OSError:
                result = False

        self.mtda.debug(3, "sdmux.samsung.write(): %s" % str(result))
        return result

def instantiate(mtda):
   return SamsungSdMuxController(mtda)
