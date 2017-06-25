# System imports
import abc
import subprocess

# Local imports
from mtda.sdmux.controller import SdMuxController

class SamsungSdMuxController(SdMuxController):

    def __init__(self):
        self.serial = "sdmux"

    def configure(self, conf):
        """ Configure this sdmux controller from the provided configuration"""
        if 'serial' in conf:
           self.serial = conf['serial']
        return

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

def instantiate():
   return SamsungSdMuxController()
