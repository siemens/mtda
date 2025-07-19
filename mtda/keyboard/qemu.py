# ---------------------------------------------------------------------------
# QEMU keyboard driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import time

# Local imports
from mtda.keyboard.controller import KeyboardController


class QemuController(KeyboardController):

    def __init__(self, mtda):
        self.mtda = mtda
        self.qemu = mtda.power

    def configure(self, conf):
        self.mtda.debug(3, "keyboard.qemu.configure()")

    def probe(self):
        self.mtda.debug(3, "keyboard.qemu.probe()")

        result = (self.qemu is not None and self.qemu.variant == "qemu")
        if result is False:
            self.mtda.debug(1, "keyboard.qemu.probe(): "
                               "a qemu power controller is required")

        self.mtda.debug(3, f"keyboard.qemu.probe(): {str(result)}")
        return result

    def idle(self):
        return True

    def press(self, key, repeat=1, ctrl=False, shift=False, alt=False,
              meta=False):
        self.mtda.debug(3, "keyboard.qemu.press()")

        symbols = {
                ',': 'comma',
                '.': 'dot',
                '*': 'asterisk',
                '/': 'slash',
                '-': 'minus',
                '=': 'equal',
                ' ': 'spc',
                '\t': 'tab',
                '\n': 'ret'
                }

        mod = ""
        if ctrl:
            mod = "ctrl-"
        if shift:
            mod = f"{mod}shift-"
        if alt:
            mod = f"{mod}alt-"
        if meta:
            mod = f"{mod}meta_l-"

        result = True
        while repeat > 0:
            repeat = repeat - 1
            key = symbols[key] if key in symbols else key
            self.qemu.cmd(f"sendkey {mod}{key}")
            time.sleep(0.1)
        return result

    def backspace(self, repeat=1, ctrl=False, shift=False, alt=False,
                  meta=False):
        self.mtda.debug(3, "keyboard.qemu.backspace()")
        return self.press("backspace", repeat, ctrl, shift, alt, meta)

    def enter(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.enter()")
        return self.press("ret", repeat, ctrl, shift, alt, meta)

    def esc(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.esc()")
        return self.press("esc", repeat, ctrl, shift, alt, meta)

    def down(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.down()")
        return self.press("down", repeat, ctrl, shift, alt, meta)

    def left(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.left()")
        return self.press("left", repeat, ctrl, shift, alt, meta)

    def capsLock(self, repeat=1, ctrl=False, shift=False, alt=False,
                 meta=False):
        self.mtda.debug(3, "keyboard.qemu.capsLock()")
        return self.press("caps_lock", repeat, ctrl, shift, alt, meta)

    def right(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.right()")
        return self.press("right", repeat, ctrl, shift, alt, meta)

    def up(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.up()")
        return self.press("up", repeat, ctrl, shift, alt, meta)

    def f1(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.f1()")
        return self.press("f1", repeat, ctrl, shift, alt, meta)

    def f2(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.f2()")
        return self.press("f2", repeat, ctrl, shift, alt, meta)

    def f3(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.f3()")
        return self.press("f3", repeat, ctrl, shift, alt, meta)

    def f4(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.f4()")
        return self.press("f4", repeat, ctrl, shift, alt, meta)

    def f5(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.f5()")
        return self.press("f5", repeat, ctrl, shift, alt, meta)

    def f6(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.f6()")
        return self.press("f6", repeat, ctrl, shift, alt, meta)

    def f7(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.f7()")
        return self.press("f7", repeat, ctrl, shift, alt, meta)

    def f8(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.f8()")
        return self.press("f8", repeat, ctrl, shift, alt, meta)

    def f9(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.f9()")
        return self.press("f9", repeat, ctrl, shift, alt, meta)

    def f10(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.f10()")
        return self.press("f10", repeat, ctrl, shift, alt, meta)

    def f11(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.f11()")
        return self.press("f11", repeat, ctrl, shift, alt, meta)

    def f12(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.f12()")
        return self.press("f12", repeat, ctrl, shift, alt, meta)

    def tab(self, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        self.mtda.debug(3, "keyboard.qemu.tab()")
        return self.press("tab", repeat, ctrl, shift, alt, meta)

    def write(self, str):
        self.mtda.debug(3, "keyboard.qemu.write()")

        for k in str:
            self.press(k)


def instantiate(mtda):
    return QemuController(mtda)
