# ---------------------------------------------------------------------------
# HID mouse driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import select
import struct

# Local imports
from mtda.mouse.controller import MouseController
from mtda.support.usb import Composite
import mtda.constants as CONSTS


class HidMouseController(MouseController):

    LEFT_BUTTON = 0x01
    RIGHT_BUTTON = 0x02
    MIDDLE_BUTTON = 0x04

    # Timeout (seconds) for writes
    TIMEOUT = 1

    def __init__(self, mtda):
        self.dev = None
        self.fd = None
        self.mtda = mtda
        Composite.mtda = mtda

    def configure(self, conf):
        self.mtda.debug(3, "mouse.hid.configure()")

        result = Composite.configure('mouse', conf)
        if 'device' in conf:
            self.dev = conf['device']
        else:
            self.dev = CONSTS.USB.HID_MOUSE
        self.mtda.debug(4, f"mouse.hid.configure(): will use {self.dev}")

        self.mtda.debug(3, f"mouse.hid.configure(): {result}")
        return result

    def probe(self):
        self.mtda.debug(3, "mouse.hid.probe()")

        result = True
        if self.dev is None:
            result = False
            self.mtda.debug(1, f"mouse.hid.probe(): {self.dev} not configured")

        self.mtda.debug(3, f"mouse.hid.probe(): {result}")
        return result

    def _write(self, report):
        self.mtda.debug(3, "mouse.hid._write()")

        if self.fd is None:
            self.mtda.debug(4, f"mouse.hid._write(): opening {self.dev}")
            self.fd = open(self.dev, mode="r+b", buffering=0)

        outs = [self.fd]
        readable, writable, error = select.select([], outs, [], self.TIMEOUT)
        if len(writable) > 0:
            result = self.fd.write(report)
        else:
            result = 0

        self.mtda.debug(3, f"mouse.hid._write(): {result}")
        return result

    def idle(self):
        self.mtda.debug(3, "mouse.hid.idle()")

        result = True
        if self.fd is not None:
            self.fd.close()
            self.fd = None

        self.mtda.debug(3, f"mouse.hid.idle(): {result}")
        return result

    def move(self, x, y, buttons=0):
        self.mtda.debug(3, f"mouse.hid.move({x}, {y}, {buttons})")

        x = int(x * CONSTS.MOUSE.MAX_X)
        y = int(y * CONSTS.MOUSE.MAX_Y)
        report = struct.pack('<BHH', buttons, x, y)

        self.mtda.debug(4, f"mouse.hid.move(): {report.hex(' ')}")
        result = self._write(report)

        self.mtda.debug(3, f"mouse.hid.move(): {result}")
        return result


def instantiate(mtda):
    return HidMouseController(mtda)
