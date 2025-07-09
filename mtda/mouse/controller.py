# ---------------------------------------------------------------------------
# Mouse interface for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import abc


class MouseController(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def configure(self, conf):
        """ Configure this mouse controller from the provided
            configuration"""
        return

    @abc.abstractmethod
    def probe(self):
        """ Check presence of the mouse controller"""
        return

    @abc.abstractmethod
    def move(self, x, y, buttons=0):
        """ Generate a move event"""
        return
