# System imports
import abc
import usb.core

# Local imports
from mtda.power.controller import PowerController

class Aviosys8800PowerController(PowerController):

    DEFAULT_USB_VID = 0x067b
    DEFAULT_USB_PID = 0x2303

    def __init__(self):
        self.dev = None
        self.vid = Aviosys8800PowerController.DEFAULT_USB_VID
        self.pid = Aviosys8800PowerController.DEFAULT_USB_PID

    def configure(self, conf):
        """ Configure this power controller from the provided configuration"""
        if 'vid' in conf:
           self.vid = int(conf['vid'], 16)
        if 'pid' in conf:
           self.pid = int(conf['pid'], 16)

    def probe(self):
        self.dev = usb.core.find(idVendor=self.vid, idProduct=self.pid)
        if self.dev is None:
            raise ValueError("Aviosys 8800 device not found!")

    def on(self):
        """ Power on the attached device"""
        return self.dev.ctrl_transfer(0x40, 0x01, 0x0001, 0xa0, [])

    def off(self):
        """ Power off the attached device"""
        return self.dev.ctrl_transfer(0x40, 0x01, 0x0001, 0x20, [])

    def status(self):
        """ Determine the current power state of the attached device"""
        ret = self.dev.ctrl_transfer(0xc0, 0x01, 0x0081, 0x0000, 0x0001)
        if ret[0] == 0xa0:
            return self.POWERED_ON
        return self.POWERED_OFF

    def toggle(self):
        """ Toggle power for the attached device"""
        s = self.status()
        if s == self.POWERED_OFF:
            self.on()
            return self.POWERED_ON
        else:
            self.off()
            return self.POWERED_OFF

def instantiate():
   return Aviosys8800PowerController()
