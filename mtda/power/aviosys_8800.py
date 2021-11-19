# ---------------------------------------------------------------------------
# aviosys power driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2021 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import abc
import threading
import usb.core

# Local imports
from mtda.power.controller import PowerController


class Aviosys8800PowerController(PowerController):

    DEFAULT_USB_VID = 0x067b
    DEFAULT_USB_PID = 0x2303

    def __init__(self, mtda):
        self.dev = None
        self.ev = threading.Event()
        self.mtda = mtda
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

    def command(self, args):
        return False

    def on(self):
        """ Power on the attached device"""
        status = self.dev.ctrl_transfer(0x40, 0x01, 0x0001, 0xa0, [])
        if status == 0:
            self.ev.set()
        return (status == 0)

    def off(self):
        """ Power off the attached device"""
        status = self.dev.ctrl_transfer(0x40, 0x01, 0x0001, 0x20, [])
        if status == 0:
            self.ev.clear()
        return (status == 0)

    def status(self):
        """ Determine the current power state of the attached device"""
        ret = self.dev.ctrl_transfer(0xc0, 0x01, 0x0081, 0x0000, 0x0001)
        if ret[0] == 0xa0:
            return self.POWER_ON
        return self.POWER_OFF

    def toggle(self):
        """ Toggle power for the attached device"""
        s = self.status()
        if s == self.POWER_OFF:
            self.on()
        else:
            self.off()
        return self.status()

    def wait(self):
        while self.status() != self.POWER_ON:
            self.ev.wait()


def instantiate(mtda):
    return Aviosys8800PowerController(mtda)
