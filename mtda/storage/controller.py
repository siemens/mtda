# ---------------------------------------------------------------------------
# Storage interface for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2021 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import abc


class StorageController(object):
    __metaclass__ = abc.ABCMeta

    SD_ON_UNSURE = "???"
    SD_ON_HOST = "HOST"
    SD_ON_TARGET = "TARGET"

    @abc.abstractmethod
    def close(self):
        """ Close the storage device"""
        return False

    @abc.abstractmethod
    def configure(self, conf):
        """ Configure this storage controller from the configuration"""
        return True

    @abc.abstractmethod
    def mount(self, part):
        """ Mount the shared storage on the host"""
        return False

    @abc.abstractmethod
    def open(self):
        """ Open the shared storage device for I/O operations"""
        return False

    @abc.abstractmethod
    def probe(self):
        """ Check presence of the shared storage device"""
        return False

    @abc.abstractmethod
    def supports_hotplug(self):
        """ Whether the shared storage device may be hot-plugged"""
        return False

    @abc.abstractmethod
    def to_host(self):
        """ Attach the shared storage device to the host"""
        return False

    @abc.abstractmethod
    def to_target(self):
        """ Attach the shared storage device to the target"""
        return False

    @abc.abstractmethod
    def status(self):
        """ Determine where the shared storage device is attached"""
        return self.SD_ON_UNSURE

    @abc.abstractmethod
    def update(self, dst, offset):
        """ Update specified file"""
        return False

    @abc.abstractmethod
    def write(self, data):
        """ Write data to the shared storage device"""
        return False
