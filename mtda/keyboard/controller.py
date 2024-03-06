# ---------------------------------------------------------------------------
# Keyboard interface for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2021 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import abc


class KeyboardController(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def configure(self, conf):
        """ Configure this keyboard controller from the provided
            configuration"""
        return

    @abc.abstractmethod
    def probe(self):
        """ Check presence of the keyboard controller"""
        return

    @abc.abstractmethod
    def idle(self):
        """ Put the keyboard controller in idle state"""
        return

    @abc.abstractmethod
    def backspace(self, repeat=1):
        return False

    @abc.abstractmethod
    def esc(self, repeat=1):
        return False

    @abc.abstractmethod
    def enter(self, repeat=1):
        return False

    @abc.abstractmethod
    def down(self, repeat=1):
        return False

    @abc.abstractmethod
    def left(self, repeat=1):
        return False

    @abc.abstractmethod
    def capsLock(self, repeat=1):
        return False

    @abc.abstractmethod
    def right(self, repeat=1):
        return False

    @abc.abstractmethod
    def up(self, repeat=1):
        return False

    @abc.abstractmethod
    def press(self, key, repeat=1, ctrl=False, shift=False, alt=False, meta=False):
        return False

    @abc.abstractmethod
    def write(self, str):
        return

    @abc.abstractmethod
    def f1(self, repeat=1):
        return False

    @abc.abstractmethod
    def f2(self, repeat=1):
        return False

    @abc.abstractmethod
    def f3(self, repeat=1):
        return False

    @abc.abstractmethod
    def f4(self, repeat=1):
        return False

    @abc.abstractmethod
    def f5(self, repeat=1):
        return False

    @abc.abstractmethod
    def f6(self, repeat=1):
        return False

    @abc.abstractmethod
    def f7(self, repeat=1):
        return False

    @abc.abstractmethod
    def f8(self, repeat=1):
        return False

    @abc.abstractmethod
    def f9(self, repeat=1):
        return False

    @abc.abstractmethod
    def f10(self, repeat=1):
        return False

    @abc.abstractmethod
    def f11(self, repeat=1):
        return False

    @abc.abstractmethod
    def f12(self, repeat=1):
        return False

    @abc.abstractmethod
    def tab(self, repeat=1):
        return False
