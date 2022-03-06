# ---------------------------------------------------------------------------
# Shell command power driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (c) Siemens AG, 2022
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import subprocess
import threading

# Local imports
from mtda.power.controller import PowerController


class ShellCmdPowerController(PowerController):

    def __init__(self, mtda):
        self.ev = threading.Event()
        self.on_cmd = None
        self.off_cmd = None
        self.check_on = None
        self.mtda = mtda

    def configure(self, conf):
        if 'on-cmd' in conf:
            self.on_cmd = conf['on-cmd']
        if 'off-cmd' in conf:
            self.off_cmd = conf['off-cmd']
        if 'check-on' in conf:
            self.check_on = conf['check-on']

    def probe(self):
        if self.on_cmd is None:
            raise ValueError("on-cmd not specified")
        self.mtda.debug(3, "on-cmd: {}".format(self.on_cmd))
        if self.off_cmd is None:
            raise ValueError("off-cmd not specified")
        self.mtda.debug(3, "off-cmd: {}".format(self.off_cmd))
        if self.check_on is None:
            raise ValueError("check-on not specified")
        self.mtda.debug(3, "check_on: {}".format(self.check_on))

    def command(self, args):
        return False

    def on(self):
        proc = subprocess.run(self.on_cmd, shell=True, capture_output=True)
        if proc.returncode != 0:
            return False
        self.ev.set()
        return True

    def off(self):
        proc = subprocess.run(self.off_cmd, shell=True, capture_output=True)
        if proc.returncode != 0:
            return False
        self.ev.clear()
        return True

    def status(self):
        proc = subprocess.run(self.check_on, shell=True, capture_output=True)
        self.mtda.debug(3, "check_on: {}".format(proc.returncode))
        if proc.returncode == 0:
            return self.POWER_ON
        elif proc.returncode == 1:
            return self.POWER_OFF
        else:
            self.POWER_UNSURE

    def toggle(self):
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
    return ShellCmdPowerController(mtda)
