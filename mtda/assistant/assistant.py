# ---------------------------------------------------------------------------
# Assistant interface for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2021 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import abc


class Assistant(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def configure(self, conf):
        """ Configure this assistant from the provided configuration"""
        return

    @abc.abstractmethod
    def probe(self):
        """ Check presence of the assistant"""
        return

    @abc.abstractmethod
    def start(self):
        """ Start the assistant"""
        return
