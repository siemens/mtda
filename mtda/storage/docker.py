# ---------------------------------------------------------------------------
# Storage interface for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import threading

# Local imports
import mtda.constants as CONSTS
from mtda.storage.controller import StorageController


class DockerController(StorageController):

    def __init__(self, mtda):
        self.mtda = mtda
        self._docker = mtda.power
        self._lock = threading.Lock()
        self._mode = CONSTS.STORAGE.ON_TARGET
        self._handle = None

    def close(self):
        self.mtda.debug(3, "storage.docker.close()")

        result = True
        with self._lock:
            if self._handle is not None:
                self._handle = None
                result = self._docker.import_close()

        self.mtda.debug(3, f"storage.docker.close(): {result}")
        return result

    def configure(self, conf):
        return True

    def mount(self, part):
        return False

    def open(self):
        self.mtda.debug(3, "storage.docker.open()")

        with self._lock:
            result = False
            if self._mode == CONSTS.STORAGE.ON_HOST:
                self._handle = self._docker.import_open()
                result = self._handle is not None

        self.mtda.debug(3, f"storage.docker.open(): {result}")
        return result

    def probe(self):
        self.mtda.debug(3, "storage.docker.probe()")
        self._lock.acquire()

        result = self._docker.variant == "docker"
        if result is False:
            self.mtda.debug(1, "storage.docker.probe(): "
                            "docker power controller required!")

        self.mtda.debug(3, f"storage.docker.probe(): {result}")
        self._lock.release()
        return result

    def supports_hotplug(self):
        return False

    def to_host(self):
        self._mode = CONSTS.STORAGE.ON_HOST
        return True

    def to_target(self):
        self._mode = CONSTS.STORAGE.ON_TARGET
        return True

    def status(self):
        return self._mode

    def update(self, dst, offset):
        raise RuntimeError('update not supported for docker')

    def write(self, data):
        self.mtda.debug(3, "storage.docker.write()")

        result = None
        with self._lock:
            if self._handle is not None:
                result = self._handle.write(data)

        self.mtda.debug(3, f"storage.docker.write(): {result}")
        return result


def instantiate(mtda):
    return DockerController(mtda)
