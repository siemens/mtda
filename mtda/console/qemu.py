# System imports
import abc
import fcntl
import os
import select

# Local imports
from mtda.console.interface import ConsoleInterface

class QemuConsole(ConsoleInterface):

    def __init__(self, mtda):
        self.mtda = mtda
        self.qemu = mtda.power_controller
        self.opened = False

    """ Configure this console from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "console.qemu.configure()")

    def probe(self):
        self.mtda.debug(3, "console.qemu.probe()")

        result = os.path.exists("/tmp/qemu-serial.out")

        self.mtda.debug(3, "console.qemu.probe(): %s" % str(result))
        return result

    def open(self):
        self.mtda.debug(3, "console.qemu.open()")

        result = self.opened
        if self.opened == False:
            try:
                self.tx = open("/tmp/qemu-serial.in",  mode="wb", buffering=0)
                self.rx = open("/tmp/qemu-serial.out", mode="rb", buffering=0)

                result = True
            finally:
                self.opened = result
        else:
            self.mtda.debug(4, "console.qemu.open(): already opened")

        self.mtda.debug(3, "console.qemu.open(): %s" % str(result))
        return result

    def close(self):
        self.mtda.debug(3, "console.qemu.close()")

        result = True

        self.mtda.debug(3, "console.qemu.close(): %s" % str(result))
        return result

    """ Return number of pending bytes to read"""
    def pending(self):
        self.mtda.debug(3, "console.qemu.pending()")

        result = 0
        if self.opened == True:
            inputs = [ self.rx ]
            readable, writable, error = select.select(inputs, [], inputs, 0)
            if len(readable) > 0:
                result = 1

        self.mtda.debug(3, "console.qemu.pending(): %s" % str(result))
        return result

    """ Read bytes from the console"""
    def read(self, n=1):
        self.mtda.debug(3, "console.qemu.read()")

        result = None
        if self.opened == True:
            try:
                result = self.rx.read(n)
            except BlockingIOError:
                result = None

        if result is None:
            result = b''

        self.mtda.debug(3, "console.qemu.read(): %s" % str(result))
        return result

    """ Write to the console"""
    def write(self, data):
        self.mtda.debug(3, "console.qemu.write(data=%s)" % str(data))

        result = None
        if self.opened == True:
            result = self.tx.write(data)

        self.mtda.debug(3, "console.qemu.write(): %s" % str(result))
        return result

def instantiate(mtda):
    return QemuConsole(mtda)
