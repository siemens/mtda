# ---------------------------------------------------------------------------
# Console interface for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2021 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import abc


class ConsoleInterface(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def configure(self, conf, role='console'):
        """ Configure this console from the provided configuration"""
        return False

    @abc.abstractmethod
    def probe(self):
        """ Check presence of the console"""
        return False

    @abc.abstractmethod
    def open(self):
        """ Open the console interface"""
        return False

    @abc.abstractmethod
    def close(self):
        """ Close the console interface"""
        return

    @abc.abstractmethod
    def pending(self):
        """ Return number of pending bytes to read"""
        return 0

    @abc.abstractmethod
    def read(self, n=1):
        """ Read from the console"""
        return 0

    @abc.abstractmethod
    def write(self, data):
        """ Write to the console"""
        return 0
