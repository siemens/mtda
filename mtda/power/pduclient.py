# ---------------------------------------------------------------------------
# pduclient power driver for MTDA
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

# Local imports
from mtda.power.controller import PowerController


class PduClientPowerController(PowerController):

    def __init__(self, mtda):
        self.dev = None
        self.daemon = None
        self.hostname = None
        self.mtda = mtda
        self.port = None
        self.state = self.POWER_UNSURE

    def configure(self, conf):
        """ Configure this power controller from the provided configuration"""
        if 'daemon' in conf:
            self.daemon = conf['daemon']
        if 'hostname' in conf:
            self.hostname = conf['hostname']
        if 'port' in conf:
            self.port = conf['port']

    def probe(self):
        if self.daemon is None:
            raise ValueError("machine running lavapdu-listen "
                             "not specified ('daemon' not set)!")
        if self.hostname is None:
            raise ValueError("pdu not specified ('hostname' not set)!")
        if self.port is None:
            raise ValueError("port not specified!")

    def cmd(self, what):
        client = "/usr/bin/pduclient"
        return os.system(
            "{0} --daemon {1} --hostname {2} --command {3} "
            "--port {4}"
            .format(client, self.daemon, self.hostname, what, self.port))

    def command(self, args):
        return False

    def on(self):
        """ Power on the attached device"""
        status = self.cmd('on')
        if status == 0:
            self.state = self.POWER_ON
            return True
        return False

    def off(self):
        """ Power off the attached device"""
        status = self.cmd('off')
        if status == 0:
            self.state = self.POWER_OFF
            return True
        return False

    def status(self):
        """ Determine the current power state of the attached device"""
        return self.state


def instantiate(mtda):
    return PduClientPowerController(mtda)
