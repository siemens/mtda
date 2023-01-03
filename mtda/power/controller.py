# ---------------------------------------------------------------------------
# Power interface for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2023 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import abc
import mtda.constants as CONSTS


class PowerController(object):
    __metaclass__ = abc.ABCMeta

    POWER_OFF = CONSTS.POWER.OFF
    POWER_ON = CONSTS.POWER.ON
    POWER_UNSURE = CONSTS.POWER.UNSURE
    POWER_LOCKED = CONSTS.POWER.LOCKED

    @abc.abstractmethod
    def configure(self, conf):
        """ Configure this power controller from the provided configuration"""
        return

    @abc.abstractmethod
    def probe(self):
        """ Check presence of the power controller"""
        return

    @abc.abstractmethod
    def command(self, args):
        """ Send a command to the device"""
        return False

    @abc.abstractmethod
    def on(self):
        """ Power on the attached device"""
        return

    @abc.abstractmethod
    def off(self):
        """ Power off the attached device"""
        return

    @abc.abstractmethod
    def status(self):
        """ Determine the current power state of the attached device"""
        return self.POWER_OFF

    @abc.abstractmethod
    def wait(self):
        """ Wait for the target to be powered on"""
        return
