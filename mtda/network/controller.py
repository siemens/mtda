# ---------------------------------------------------------------------------
# Network interface for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import abc


class NetworkController(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def configure(self, conf):
        """ Configure this network controller from the provided configuration"""
        return

    @abc.abstractmethod
    def probe(self):
        """ Check presence of the network controller"""
        return

    @abc.abstractmethod
    def up(self):
        """ Bring-up the network interface"""
        return

    @abc.abstractmethod
    def down(self):
        """ Bring-down the network interface"""
        return
