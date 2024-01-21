# ---------------------------------------------------------------------------
# USB Function console driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2024 Siemens Digital Industries Software
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
        self.hotplug = True
        self.port = None
        self.rate = 9600
        Composite.mtda = mtda

    def configure(self, conf, role='console'):
        self.mtda.debug(3, "console.usbf.configure()")

        super().configure(conf)
        if self.port is None:
            self.port = "/dev/ttyGS0" if role == "console" else "/dev/ttyGS1"
        result = Composite.configure(role, conf)

        self.mtda.debug(3, f"console.usbf.configure(): {result}")
        return result

    def configure_systemd(self, dir):
        return None


def instantiate(mtda):
    return UsbFunctionConsole(mtda)
