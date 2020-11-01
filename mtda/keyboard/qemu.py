# ---------------------------------------------------------------------------
# QEMU keyboard driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (c) Mentor, a Siemens business, 2017-2020
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import abc
import os
import sys
import time

# Local imports
from mtda.keyboard.controller import KeyboardController


class QemuController(KeyboardController):

    def __init__(self, mtda):
        self.mtda = mtda
        self.qemu = mtda.power_controller

    def configure(self, conf):
        self.mtda.debug(3, "keyboard.qemu.configure()")

    def probe(self):
        self.mtda.debug(3, "keyboard.qemu.probe()")

        result = self.qemu.variant == "qemu"
        if result is False:
            self.mtda.debug(1, "keyboard.qemu.probe(): "
                               "a qemu power controller is required")

        self.mtda.debug(3, "keyboard.qemu.probe(): %s" % str(result))
        return result

    def idle(self):
        return True

    def press(self, key, repeat=1):
        self.mtda.debug(3, "keyboard.qemu.press()")

        result = True
        while repeat > 0:
            repeat = repeat - 1
            self.qemu.cmd("sendkey %s" % key)
            time.sleep(0.1)
        return result

    def enter(self, repeat=1):
        self.mtda.debug(3, "keyboard.qemu.enter()")
        return self.press("ret", repeat)

    def esc(self, repeat=1):
        self.mtda.debug(3, "keyboard.qemu.esc()")
        return self.press("esc", repeat)

    def down(self, repeat=1):
        self.mtda.debug(3, "keyboard.qemu.down()")
        return self.press("down", repeat)

    def left(self, repeat=1):
        self.mtda.debug(3, "keyboard.qemu.left()")
        return self.press("left", repeat)

    def right(self, repeat=1):
        self.mtda.debug(3, "keyboard.qemu.right()")
        return self.press("right", repeat)

    def up(self, repeat=1):
        self.mtda.debug(3, "keyboard.qemu.up()")
        return self.press("up", repeat)

    def write(self, str):
        self.mtda.debug(3, "keyboard.qemu.write()")


def instantiate(mtda):
    return QemuController(mtda)
