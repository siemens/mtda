# ---------------------------------------------------------------------------
# HID keyboard driver for MTDA
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
import select
import time

# Local imports
from mtda.keyboard.controller import KeyboardController
from mtda.support.usb import Composite
import mtda.constants as CONSTS


class HidKeyboardController(KeyboardController):

    KEY_MOD_LCTRL = 0x01
    KEY_MOD_LSHIFT = 0x02
    KEY_MOD_LALT = 0x04
    KEY_MOD_LMETA = 0x08

    # Timeout (seconds) for writes
    TIMEOUT = 1

    def __init__(self, mtda):
        self.dev = None
        self.fd = None
        self.mtda = mtda
        Composite.mtda = mtda

    def configure(self, conf):
        self.mtda.debug(3, "keyboard.hid.configure()")

        result = Composite.configure('keyboard', conf)
        if 'device' in conf:
            self.dev = conf['device']
        else:
            self.dev = CONSTS.USB.HID_KEYBOARD
        self.mtda.debug(4, "keyboard.hid."
                           f"configure(): will use {self.dev}")

        self.mtda.debug(3, f"keyboard.hid.configure(): {result}")
        return result

    def probe(self):
        self.mtda.debug(3, "keyboard.hid.probe()")

        result = True
        if self.dev is None:
            result = False
            self.mtda.debug(1, "keyboard.hid."
                               f"probe(): {self.dev} not configured")

        self.mtda.debug(3, f"keyboard.hid.probe(): {result}")
        return result

    def write_report(self, report):
        self.mtda.debug(3, "keyboard.hid.write_report()")

        outs = [self.fd]
        readable, writable, error = select.select([], outs, [], self.TIMEOUT)
        if len(writable) > 0:
            result = self.fd.write(report.encode())
        else:
            result = 0

        self.mtda.debug(3, f"keyboard.hid.write_report(): {result}")
        return result

    def idle(self):
        self.mtda.debug(3, "keyboard.hid.idle()")

        result = True
        if self.fd is not None:
            self.fd.close()
            self.fd = None

        self.mtda.debug(3, f"keyboard.hid.idle(): {result}")
        return result

    def press(self, key, repeat=1, ctrl=False, shift=False, alt=False,
              meta=False):
        self.mtda.debug(3, "keyboard.hid.press()")

        bsl = '\\'
        bsp = '\b'
        ret = '\n'
        lower_keys = {
            'a': 0x04, 'b': 0x05, 'c': 0x06, 'd': 0x07, 'e': 0x08, 'f': 0x09,
            'g': 0x0a, 'h': 0x0b, 'i': 0x0c, 'j': 0x0d, 'k': 0x0e, 'l': 0x0f,
            'm': 0x10, 'n': 0x11, 'o': 0x12, 'p': 0x13, 'q': 0x14, 'r': 0x15,
            's': 0x16, 't': 0x17, 'u': 0x18, 'v': 0x19, 'w': 0x1a, 'x': 0x1b,
            'y': 0x1c, 'z': 0x1d, '1': 0x1e, '2': 0x1f, '3': 0x20, '4': 0x21,
            '5': 0x22, '6': 0x23, '7': 0x24, '8': 0x25, '9': 0x26, '0': 0x27,
            ret: 0x28, bsp: 0x2a, ' ': 0x2c, '-': 0x2d, '=': 0x2e, '[': 0x2f,
            ']': 0x30, bsl: 0x31, ';': 0x33, "'": 0x34, '`': 0x35, ',': 0x36,
            '.': 0x37, '/': 0x38
        }
        shift_keys = {
            'A': 0x04, 'B': 0x05, 'C': 0x06, 'D': 0x07, 'E': 0x08, 'F': 0x09,
            'G': 0x0a, 'H': 0x0b, 'I': 0x0c, 'J': 0x0d, 'K': 0x0e, 'L': 0x0f,
            'M': 0x10, 'N': 0x11, 'O': 0x12, 'P': 0x13, 'Q': 0x14, 'R': 0x15,
            'S': 0x16, 'T': 0x17, 'U': 0x18, 'V': 0x19, 'W': 0x1a, 'X': 0x1b,
            'Y': 0x1c, 'Z': 0x1d, '!': 0x1e, '@': 0x1f, '#': 0x20, '$': 0x21,
            '%': 0x22, '^': 0x23, '&': 0x24, '*': 0x25, '(': 0x26, ')': 0x27,
            '_': 0x2d, '+': 0x2e, '{': 0x2f, '}': 0x30, '|': 0x31, ':': 0x33,
            '"': 0x34, '~': 0x35, '<': 0x36, '>': 0x37, '?': 0x38
        }

        if key in lower_keys:
            return self.send(lower_keys[key], repeat, ctrl, shift, alt, meta)
        elif key in shift_keys:
            return self.send(shift_keys[key], repeat, ctrl, True, alt, meta)

    def send(self, key, repeat=1, ctrl=False, shift=False, alt=False,
             meta=False):
        self.mtda.debug(3, "keyboard.hid.send()")

        if os.path.exists(self.dev) is False:
            self.mtda.debug(1, f"keyboard.hid.send(): {self.dev} not found")
            return False

        if self.fd is None:
            self.mtda.debug(4, f"keyboard.hid.send(): opening {self.dev}")
            self.fd = open(self.dev, mode="r+b", buffering=0)

        mod = 0x00
        if ctrl:
            mod = mod | self.KEY_MOD_LCTRL
        if shift:
            mod = mod | self.KEY_MOD_LSHIFT
        if alt:
            mod = mod | self.KEY_MOD_LALT
        if meta:
            mod = mod | self.KEY_MOD_LMETA

        self.mtda.debug(4, f"keyboard.hid.send(): mod: {mod} key: {key}")

        NULL_CHAR = chr(0)
        result = True
        while repeat > 0:
            repeat = repeat - 1
            try:
                written = self.write_report(
                    chr(mod) + NULL_CHAR + chr(key) + NULL_CHAR * 5)
                time.sleep(0.1)
                self.write_report(NULL_CHAR * 8)
                if repeat > 0:
                    time.sleep(0.1)
                if written < 8:
                    result = False
                    break
            except IOError:
                self.write_report(NULL_CHAR * 8)
                result = False
                break
        return result

    def backspace(self, repeat=1, ctrl=False, shift=False, alt=False,
                  meta=False):
        self.mtda.debug(3, "keyboard.hid.backspace()")
        return self.send(0x2a, repeat, ctrl, shift, alt, meta)

    def capsLock(self, repeat=1, ctrl=False, shift=False, alt=False,
                 meta=False):
        self.mtda.debug(3, "keyboard.hid.capsLock()")
        return self.send(0x39, repeat, ctrl, shift, alt, meta)

    def enter(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.enter()")
        return self.send(0x28, repeat, ctrl, shift, alt, meta)

    def esc(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.esc()")
        return self.send(0x29, repeat, ctrl, shift, alt, meta)

    def down(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.down()")
        return self.send(0x51, repeat, ctrl, shift, alt, meta)

    def left(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.left()")
        return self.send(0x50, repeat, ctrl, shift, alt, meta)

    def right(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.right()")
        return self.send(0x4f, repeat, ctrl, shift, alt, meta)

    def up(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.up()")
        return self.send(0x52, repeat, ctrl, shift, alt, meta)

    def f1(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.f1()")
        return self.send(0x3a, repeat, ctrl, shift, alt, meta)

    def f2(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.f2()")
        return self.send(0x3b, repeat, ctrl, shift, alt, meta)

    def f3(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.f3()")
        return self.send(0x3c, repeat, ctrl, shift, alt, meta)

    def f4(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.f4()")
        return self.send(0x3d, repeat, ctrl, shift, alt, meta)

    def f5(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.f5()")
        return self.send(0x3e, repeat, ctrl, shift, alt, meta)

    def f6(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.f6()")
        return self.send(0x3f, repeat, ctrl, shift, alt, meta)

    def f7(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.f7()")
        return self.send(0x40, repeat, ctrl, shift, alt, meta)

    def f8(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.f8()")
        return self.send(0x41, repeat, ctrl, shift, alt, meta)

    def f9(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.f9()")
        return self.send(0x42, repeat, ctrl, shift, alt, meta)

    def f10(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.f10())")
        return self.send(0x43, repeat, ctrl, shift, alt, meta)

    def f11(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.f11()")
        return self.send(0x44, repeat, ctrl, shift, alt, meta)

    def f12(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.f12()")
        return self.send(0x45, repeat, ctrl, shift, alt, meta)

    def tab(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.hid.tab()")
        return self.send(0x2b, repeat, ctrl, shift, alt, meta)

    def write(self, what):
        self.mtda.debug(3, "keyboard.hid.write()")

        for k in what:
            self.press(k)


def instantiate(mtda):
    return HidKeyboardController(mtda)
