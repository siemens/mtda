# ---------------------------------------------------------------------------
# USB Function console driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# Local imports
from mtda.console.serial import SerialConsole
from mtda.support.usb import Composite


class UsbFunctionConsole(SerialConsole):

    def __init__(self, mtda):
        super().__init__(mtda)
        self.port = "/dev/ttyGS0"
        self.rate = 9600

    def configure(self, conf):
        self.mtda.debug(3, "console.usbf.configure()")

        super().configure(conf)
        result = Composite.configure('console', conf)

        self.mtda.debug(3, "console.usbf.configure(): {}".format(result))
        return result

    def probe(self):
        self.mtda.debug(3, "console.usbf.probe()")

        result = Composite.install()
        if result is True:
            result = super().probe()

        self.mtda.debug(3, "console.usbf.probe(): {}".format(result))
        return result


def instantiate(mtda):
    return UsbFunctionConsole(mtda)
