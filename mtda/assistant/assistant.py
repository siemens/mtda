# ---------------------------------------------------------------------------
# Assistant interface for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (c) Mentor, a Siemens business, 2017-2020
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
