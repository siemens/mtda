# ---------------------------------------------------------------------------
# USB Function network driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import os
import subprocess

# Local imports
from mtda.network.controller import NetworkController
from mtda.support.usb import Composite


class UsbFunctionController(NetworkController):

    def __init__(self, mtda):
        self.device = None
        self.ipv4 = "192.168.7.1/24"
        self.mtda = mtda
        Composite.mtda = mtda

    """ Configure this network controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "network.usbf.configure()")

        if 'ipv4' in conf:
            self.ipv4 = conf['ipv4']

        result = Composite.configure('network', conf)

        self.mtda.debug(3, f"network.usbf.configure(): {result}")
        return result

    def probe(self):
        return True

    """ Bring-up the network interface"""
    def up(self):
        self.mtda.debug(3, "network.usbf.up()")

        ifname = os.path.join(Composite.path, "functions/ecm.usb0/ifname")
        if os.path.exists(ifname) is True:
            with open(ifname) as f:
                self.device = f.read().strip()
                self.mtda.debug(2, f"network.usbf.up: device is {self.device}")
        else:
            raise RuntimeError(f'{ifname} does not exist!')

        cmd = ["/sbin/ip", "addr", "add", self.ipv4, "dev",  self.device]
        subprocess.check_call(cmd)

        cmd = ["/sbin/ip", "link", "set", "dev", self.device, "up"]
        subprocess.check_call(cmd)

    """ Bring-down the network interface"""
    def down(self):
        self.mtda.debug(3, "network.usbf.down()")

        if self.device:
            self.mtda.debug(2, f"network.usbf.down: bringing {self.device} down")
            cmd = ["/sbin/ip", "link", "set", "dev", self.device, "down"]
            subprocess.check_call(cmd)
            self.device = None


def instantiate(mtda):
    return UsbFunctionController(mtda)
