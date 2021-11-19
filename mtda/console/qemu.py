# ---------------------------------------------------------------------------
# QEMU console driver for MTDA
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
import array
import fcntl
import os
import termios

# Local imports
from mtda.console.interface import ConsoleInterface


class QemuConsole(ConsoleInterface):

    def __init__(self, mtda):
        self.mtda = mtda
        self.qemu = mtda.power_controller
        self.opened = False

    """ Configure this console from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "console.qemu.configure()")

    def probe(self):
        self.mtda.debug(3, "console.qemu.probe()")
        result = self.qemu.variant == "qemu"
        self.mtda.debug(3, "console.qemu.probe(): %s" % str(result))
        return result

    def open(self):
        self.mtda.debug(3, "console.qemu.open()")

        result = self.opened
        if self.opened is False:
            try:
                self.tx = open("/tmp/qemu-serial.in",  mode="wb", buffering=0)
                self.rx = open("/tmp/qemu-serial.out", mode="rb", buffering=0)

                result = True
            finally:
                self.opened = result
        else:
            self.mtda.debug(4, "console.qemu.open(): already opened")

        self.mtda.debug(3, "console.qemu.open(): %s" % str(result))
        return result

    def close(self):
        self.mtda.debug(3, "console.qemu.close()")

        result = True

        self.mtda.debug(3, "console.qemu.close(): %s" % str(result))
        return result

    """ Return number of pending bytes to read"""
    def pending(self):
        self.mtda.debug(3, "console.qemu.pending()")

        result = 0
        if self.opened is True:
            avail = array.array('l', [0])
            fcntl.ioctl(self.rx, termios.FIONREAD, avail, 1)
            result = avail[0]

        self.mtda.debug(3, "console.qemu.pending(): %s" % str(result))
        return result

    """ Read bytes from the console"""
    def read(self, n=1):
        self.mtda.debug(3, "console.qemu.read()")

        result = None
        if self.opened is True:
            try:
                result = self.rx.read(n)
            except BlockingIOError:
                result = None

        if result is None:
            result = b''

        self.mtda.debug(3, "console.qemu.read(): %s" % str(result))
        return result

    """ Write to the console"""
    def write(self, data):
        self.mtda.debug(3, "console.qemu.write(data=%s)" % str(data))

        result = None
        if self.opened is True:
            result = self.tx.write(data)

        self.mtda.debug(3, "console.qemu.write(): %s" % str(result))
        return result


def instantiate(mtda):
    return QemuConsole(mtda)
