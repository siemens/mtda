# System imports
import abc
import os
import psutil
import subprocess

# Local imports
from mtda.sdmux.controller import SdMuxController

class SamsungSdMuxController(SdMuxController):

    def __init__(self):
        self.device = "/dev/sda"
        self.handle = None
        self.serial = "sdmux"

    def close(self):
        if self.handle is not None:
            self.handle.close()
            self.handle = None
            try:
                subprocess.check_output(["sync"])
            except subprocess.CalledProcessError:
                return False
        return True

    def configure(self, conf):
        """ Configure this sdmux controller from the provided configuration"""
        if 'device' in conf:
           self.device = conf['device']
        if 'serial' in conf:
           self.serial = conf['serial']
        return

    def mount(self, part=None):
        if self.status() != self.SD_ON_HOST:
            return False
        path = self.device
        if part:
            path = path + part
        mountpoint = os.path.join("/media", "mtda", os.path.basename(path))
        if os.path.ismount(mountpoint):
            return True
        try:
            os.makedirs(mountpoint, exist_ok=True)
            subprocess.check_call(["/bin/mount", path, mountpoint])
            return True
        except subprocess.CalledProcessError:
            return False

    def open(self):
        if self.status() != self.SD_ON_HOST:
            return False

        if self.handle is None:
            try:
                self.handle = open(self.device, "r+b")
                return True
            except:
                return False

    def probe(self):
        """ Check presence of the sdmux controller"""
        try:
            subprocess.check_output([
                "sd-mux-ctrl", "-e", self.serial, "-t"
            ])
            return True
        except subprocess.CalledProcessError:
            return False

    def to_host(self):
        """ Attach the SD card to the host"""
        try:
            subprocess.check_output([
                "sd-mux-ctrl", "-e", self.serial, "--ts"
            ])
            return True
        except subprocess.CalledProcessError:
            return False

    def to_target(self):
        """ Attach the SD card to the target"""
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
            return True
        except subprocess.CalledProcessError:
            return False

    def status(self):
        """ Determine where is the SD card attached"""
        try:
            status = subprocess.check_output([
                "sd-mux-ctrl", "-e", self.serial, "-u"
            ]).decode("utf-8").splitlines()
            for s in status:
                if s == "SD connected to: TS":
                    return self.SD_ON_HOST
                if s == "SD connected to: DUT":
                    return self.SD_ON_TARGET
            return self.SD_ON_UNSURE
        except subprocess.CalledProcessError:
            return self.SD_ON_UNSURE

    def _locate(self, dst):
        mountpoint = os.path.join("/media", "mtda", os.path.basename(self.device))
        partitions = psutil.disk_partitions()
        for p in partitions:
            if p.mountpoint.startswith(mountpoint):
                path = os.path.join(p.mountpoint, dst)
                if os.path.exists(path):
                    return path
        return None

    def update(self, dst, offset, data):
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
        return result

    def write(self, data):
        if self.handle is None:
            return False
        try:
            self.handle.write(data)
            return True
        except OSError:
            return False

def instantiate():
   return SamsungSdMuxController()
