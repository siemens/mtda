# System imports
import abc
import os
import pathlib
import threading

# Local imports
from mtda.usb.switch import UsbSwitch


class QemuMassStorageSwitch(UsbSwitch):

    def __init__(self, mtda):
        self.mtda = mtda
        self.file = "usb-mass-storage.img"
        self.id = None
        self.lock = threading.Lock()
        self.name = "mass-storage"
        self.qemu = mtda.power_controller

    def configure(self, conf):
        self.mtda.debug(3, "usb.qemu_mass_storage.configure()")

        result = True
        self.lock.acquire()
        if 'file' in conf:
            self.file = os.path.realpath(conf['file'])
            if os.path.exists(self.file) is False:
                sparse = pathlib.Path(self.file)
                sparse.touch()
                os.truncate(str(sparse), 8*1024*1024*1024)
        if 'name' in conf:
            self.name = conf['name']

        self.mtda.debug(3, "usb.qemu_mass_storage.configure(): "
                        "%s" % str(result))
        self.lock.release()
        return result

    def probe(self):
        self.mtda.debug(3, "usb.qemu_mass_storage.probe()")

        result = self.qemu.variant == "qemu"
        if result is False:
            self.mtda.debug(1, "usb.qemu_mass_storage.probe(): "
                            "qemu power controller required!")

        self.mtda.debug(3, "usb.qemu_mass_storage.probe(): %s" % str(result))
        return result

    def on(self):
        self.mtda.debug(3, "usb.qemu_mass_storage.on()")

        result = True
        self.lock.acquire()
        if self.id is None:
            self.id = self.qemu.usb_add(self.name, self.file)
            if self.id is None:
                self.mtda.debug(1, "usb.qemu_mass_storage.add(): "
                                "usb storage could not be added!")
                result = False

        self.mtda.debug(3, "usb.qemu_mass_storage.add(): %s" % str(result))
        self.lock.release()
        return result

    def off(self):
        self.mtda.debug(3, "usb.qemu_mass_storage.off()")

        result = True
        self.lock.acquire()
        if self.id is not None:
            result = self.qemu.usb_rm(self.name)
            if result is True:
                self.id = None
            else:
                self.mtda.debug(1, "usb.qemu_mass_storage.off(): "
                                "usb storage could not be removed!")

        self.mtda.debug(3, "usb.qemu_mass_storage.off(): %s" % str(result))
        self.lock.release()
        return result

    def status(self):
        self.mtda.debug(3, "usb.qemu_mass_storage.status()")

        self.lock.acquire()
        result = self.POWERED_ON
        if self.id is None:
            result = self.POWERED_OFF

        self.mtda.debug(3, "usb.qemu_mass_storage.status(): %s" % str(result))
        self.lock.release()
        return result

    def toggle(self):
        self.mtda.debug(3, "usb.qemu_mass_storage.toggle()")
        s = self.status()
        if s == self.POWERED_ON:
            self.off()
            result = self.POWERED_OFF
        else:
            self.on()
            result = self.POWERED_ON

        self.mtda.debug(3, "usb.qemu_mass_storage.toggle(): %s" % str(result))
        return result


def instantiate(mtda):
    return QemuMassStorageSwitch(mtda)
