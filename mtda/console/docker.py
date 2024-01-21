# ---------------------------------------------------------------------------
# docker console driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2024 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import array
import fcntl
import os
import select
import termios

# Local imports
from mtda.console.interface import ConsoleInterface


class DockerConsole(ConsoleInterface):

    def __init__(self, mtda):
        self.mtda = mtda
        self.docker = mtda.power
        self._fd = None
        self._opened = False
        self._socket = None

    """ Configure this console from the provided configuration"""
    def configure(self, conf, role='console'):
        self.mtda.debug(3, "console.docker.configure()")

    def probe(self):
        self.mtda.debug(3, "console.docker.probe()")
        result = self.docker.variant == "docker"
        self.mtda.debug(3, f"console.docker.probe(): {result}")
        return result

    def open(self):
        self.mtda.debug(3, "console.docker.open()")

        result = self._opened
        if self._opened is False:
            self._socket = self.docker.socket()
            if self._socket is not None:
                self._fd = self._socket.fileno()
                result = True
            else:
                self.mtda.debug(1, "console.docker.open(): "
                                "could not attach to container socket")
        else:
            self.mtda.debug(4, "console.docker.open(): already opened")

        self._opened = result
        self.mtda.debug(3, f"console.docker.open(): {result}")
        return result

    def close(self):
        self.mtda.debug(3, "console.docker.close()")

        result = True
        if self._opened is True:
            self._socket.close()
            self._fd = None
            self._socket = None
            self._opened = False

        self.mtda.debug(3, f"console.docker.close(): {result}")
        return result

    """ Return number of pending bytes to read"""
    def pending(self):
        self.mtda.debug(3, "console.docker.pending()")

        result = 0
        if self._opened is True:
            avail = array.array('l', [0])
            fcntl.ioctl(self._fd, termios.FIONREAD, avail, 1)
            result = avail[0]

        self.mtda.debug(3, f"console.docker.pending(): {result}")
        return result

    """ Read bytes from the console"""
    def read(self, n=1):
        self.mtda.debug(3, f"console.docker.read({n})")

        result = None
        if self._opened is True:
            inputs = [self._socket]
            outputs = []
            readable, writable, error = select.select(inputs, outputs, inputs)
            if len(readable) > 0 and self._fd is not None:
                result = os.read(self._fd, n)
        else:
            self.mtda.debug(1, "console.docker.read(): not opened!")

        if result is None:
            result = b''

        self.mtda.debug(3, f"console.docker.read(): {result}")
        return result

    """ Write to the console"""
    def write(self, data):
        self.mtda.debug(3, f"console.docker.write(data={data})")

        result = None
        if self._opened is True:
            result = os.write(self._fd, data)

        self.mtda.debug(3, f"console.docker.write(): {result}")
        return result


def instantiate(mtda):
    return DockerConsole(mtda)
