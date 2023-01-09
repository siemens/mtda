# ---------------------------------------------------------------------------
# Serial console driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2023 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import os
import serial

# Local imports
from mtda.console.interface import ConsoleInterface


class SerialConsole(ConsoleInterface):

    def __init__(self, mtda):
        self.ser = None
        self.mtda = mtda
        self.port = "/dev/ttyUSB0"
        self.rate = 115200
        self.opened = False
        self.role = 'console'
        self.hotplug = False

    """ Configure this console from the provided configuration"""
    def configure(self, conf, role='console'):
        self.mtda.debug(3, "console.serial.configure()")

        if 'port' in conf:
            self.port = conf['port']
        if 'rate' in conf:
            self.rate = int(conf['rate'], 10)
        self.role = role

    def configure_systemd(self, dir):
        self.mtda.debug(3, "console.serial.configure_systemd()")

        result = None
        if self.port is not None:
            device = os.path.basename(self.port)
            dropin = os.path.join(dir, 'auto-dep-{}.conf'.format(self.role))
            with open(dropin, 'w') as f:
                f.write('[Unit]\n')
                f.write('Wants=dev-{}.device\n'.format(device))
                f.write('After=dev-{}.device\n'.format(device))

        self.mtda.debug(3, "console.serial.configure_systemd(): "
                           "{}".format(result))
        return result

    def probe(self):
        self.mtda.debug(3, "console.serial.probe()")

        result = True
        if self.hotplug is False:
            result = os.path.exists(self.port)
        if result is True:
            self.ser = serial.Serial()
            self.ser.port = self.port
            self.ser.baudrate = self.rate
        else:
            self.mtda.debug(1, "console.serial.probe(): "
                            "{} does not exist".format(self.port))

        self.mtda.debug(3, "console.serial.probe(): {}".format(result))
        return result

    def open(self):
        self.mtda.debug(3, "console.serial.open()")

        if self.ser is not None:
            if self.opened is False:
                self.ser.open()
                self.opened = True
            else:
                self.mtda.debug(4, "console.serial.open(): already opened")
        else:
            self.mtda.debug(0, "serial console not setup!")

        result = self.opened

        self.mtda.debug(3, "console.serial.open(): %s" % str(result))
        return result

    def close(self):
        self.mtda.debug(3, "console.serial.close()")

        if self.opened is True:
            if self.ser is not None:
                self.ser.cancel_read()
                self.ser.close()
                self.opened = False
            else:
                self.mtda.debug(0, "lost handle of opened serial console!")
        else:
            self.mtda.debug(4, "console.serial.close(): already closed")

        result = self.opened is False
        self.mtda.debug(3, "console.serial.close(): {}".format(result))
        return result

    """ Return number of pending bytes to read"""
    def pending(self):
        self.mtda.debug(3, "console.serial.pending()")

        result = 0
        if self.ser is not None and self.opened is True:
            result = self.ser.inWaiting()

        self.mtda.debug(3, "console.serial.pending(): %s" % str(result))
        return result

    """ Read bytes from the console"""
    def read(self, n=1):
        self.mtda.debug(3, "console.serial.read()")

        result = None
        if self.ser is not None and self.opened is True:
            result = self.ser.read(n)

        self.mtda.debug(3, "console.serial.read(): %s" % str(result))
        return result

    """ Write to the console"""
    def write(self, data):
        self.mtda.debug(3, "console.serial.write(data=%s)" % str(data))

        result = None
        if self.ser is not None and self.opened is True:
            result = self.ser.write(data)

        self.mtda.debug(3, "console.serial.write(): %s" % str(result))
        return result


def instantiate(mtda):
    return SerialConsole(mtda)
