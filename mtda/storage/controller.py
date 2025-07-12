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
import mtda.constants as CONSTS


class StorageController(object):
    __metaclass__ = abc.ABCMeta

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
    def path(self):
        """ Expose path to the shared storage device"""
        return None

    @abc.abstractmethod
    def probe(self):
        """ Check presence of the shared storage device"""
        return False

    @abc.abstractmethod
    def setBmap(self, bmapDict):
        """ set up the bmapDict for writing the image faster"""
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
        return CONSTS.STORAGE.UNKNOWN

    @abc.abstractmethod
    def tell(self):
        """ Return position within the storage"""
        return None

    @abc.abstractmethod
    def update(self, dst, offset):
        """ Update specified file"""
        return False

    @abc.abstractmethod
    def write(self, data):
        """ Write data to the shared storage device"""
        return False

    def commit(self):
        raise RuntimeError('commit is not supported')

    def rollback(self):
        raise RuntimeError('rollback is not supported')
