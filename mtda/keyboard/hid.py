# ---------------------------------------------------------------------------
# HID keyboard driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
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


class HidKeyboardController(KeyboardController):

    KEY_MOD_LSHIFT = 0x02

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
            self.mtda.debug(4, "keyboard.hid.configure(): "
                               "will use {}".format(self.dev))

        self.mtda.debug(3, "keyboard.hid.configure(): {}".format(result))
        return result

    def probe(self):
        self.mtda.debug(3, "keyboard.hid.probe()")

        result = True
        if self.dev is None:
            result = False
            self.mtda.debug(1, "keyboard.hid.probe(): "
                               "{} not configured".format(self.dev))

        self.mtda.debug(3, "keyboard.hid.probe(): {}".format(result))
        return result

    def write_report(self, report):
        self.mtda.debug(3, "keyboard.hid.write_report()")

        outs = [self.fd]
        readable, writable, error = select.select([], outs, [], self.TIMEOUT)
        if len(writable) > 0:
            result = self.fd.write(report.encode())
        else:
            result = 0

        self.mtda.debug(3, "keyboard.hid.write_report(): {}".format(result))
        return result

    def idle(self):
        self.mtda.debug(3, "keyboard.hid.idle()")

        result = True
        if self.fd is not None:
            self.fd.close()
            self.fd = None

        self.mtda.debug(3, "keyboard.hid.idle(): {}".format(result))
        return result

    def press(self, key, mod=0x00, repeat=1):
        self.mtda.debug(3, "keyboard.hid.press()")

        if os.path.exists(self.dev) is False:
            self.mtda.debug(1, "keyboard.hid.press(): "
                               "{} not found".format(self.dev))
            return False

        if self.fd is None:
            self.mtda.debug(4, "keyboard.hid.press(): "
                               "opening {}".format(self.dev))
            self.fd = open(self.dev, mode="r+b", buffering=0)

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

    def backspace(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.backspace()")

        return self.press(0x2a, 0, repeat)

    def capsLock(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.capsLock()")

        return self.press(0x39, 0, repeat)

    def enter(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.enter()")

        return self.press(0x28, 0, repeat)

    def esc(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.esc()")

        return self.press(0x29, 0, repeat)

    def down(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.down()")

        return self.press(0x51, 0, repeat)

    def left(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.left()")

        return self.press(0x50, 0, repeat)

    def right(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.right()")

        return self.press(0x4f, 0, repeat)

    def up(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.up()")

        return self.press(0x52, 0, repeat)

    def f1(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.f1()")

        return self.press(0x3a, 0, repeat)

    def f2(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.f2()")

        return self.press(0x3b, 0, repeat)

    def f3(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.f3()")

        return self.press(0x3c, 0, repeat)

    def f4(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.f4()")

        return self.press(0x3d, 0, repeat)

    def f5(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.f5()")

        return self.press(0x3e, 0, repeat)

    def f6(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.f6()")

        return self.press(0x3f, 0, repeat)

    def f7(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.f7()")

        return self.press(0x40, 0, repeat)

    def f8(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.f8()")

        return self.press(0x41, 0, repeat)

    def f9(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.f9()")

        return self.press(0x42, 0, repeat)

    def f10(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.f10())")

        return self.press(0x43, 0, repeat)

    def f11(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.f11()")

        return self.press(0x44, 0, repeat)

    def f12(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.f12()")

        return self.press(0x45, 0, repeat)

    def tab(self, repeat=1):
        self.mtda.debug(3, "keyboard.hid.tab()")

        return self.press(0x2b, 0, repeat)

    def write(self, what):
        self.mtda.debug(3, "keyboard.hid.write()")

        ret = '\n'
        lower_keys = {
            'a': 0x04, 'b': 0x05, 'c': 0x06, 'd': 0x07, 'e': 0x08, 'f': 0x09,
            'g': 0x0a, 'h': 0x0b, 'i': 0x0c, 'j': 0x0d, 'k': 0x0e, 'l': 0x0f,
            'm': 0x10, 'n': 0x11, 'o': 0x12, 'p': 0x13, 'q': 0x14, 'r': 0x15,
            's': 0x16, 't': 0x17, 'u': 0x18, 'v': 0x19, 'w': 0x1a, 'x': 0x1b,
            'y': 0x1c, 'z': 0x1d, '1': 0x1e, '2': 0x1f, '3': 0x20, '4': 0x21,
            '5': 0x22, '6': 0x23, '7': 0x24, '8': 0x25, '9': 0x26, '0': 0x27,
            ret: 0x28, ' ': 0x2c, '-': 0x2d, '=': 0x2e
        }
        shift_keys = {
            '!': 0x1e, '@': 0x1f, '#': 0x20, '$': 0x21, '%': 0x22, '^': 0x23,
            '&': 0x24, '*': 0x25, '(': 0x26, ')': 0x27, '_': 0x2d, '+': 0x2e
        }
        special_keys = {
            '<down>': 0x51,
            '<enter>': 0x28,
            '<esc>': 0x29,
            '<f1>': 0x3a,
            '<f2>': 0x3b,
            '<f3>': 0x3c,
            '<f4>': 0x3d,
            '<f5>': 0x3e,
            '<f6>': 0x3f,
            '<f7>': 0x40,
            '<f8>': 0x41,
            '<f9>': 0x42,
            '<f10>': 0x43,
            '<f11>': 0x44,
            '<f12>': 0x45,
            '<left>': 0x50,
            '<right>': 0x4f,
            '<up>': 0x52
        }

        if what in special_keys:
            return self.press(special_keys[what])

        for k in what:
            if k in lower_keys:
                self.press(lower_keys[k])
            elif k in shift_keys:
                self.press(shift_keys[k], mod=self.KEY_MOD_LSHIFT)


def instantiate(mtda):
    return HidKeyboardController(mtda)
