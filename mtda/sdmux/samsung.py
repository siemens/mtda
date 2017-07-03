# System imports
import abc
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
