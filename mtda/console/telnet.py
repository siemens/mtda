# System imports
import abc
import socket
import time
from telnetlib import Telnet

# Local imports
from mtda.console.interface import ConsoleInterface


class TelnetConsole(ConsoleInterface):

    def __init__(self, mtda):
        self.telnet = None
        self.host = "localhost"
        self.mtda = mtda
        self.port = 23
        self.opened = False
        self.delay = 5
        self.timeout = 10

    """ Configure this console from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "console.telnet.configure()")

        if 'host' in conf:
            self.host = conf['host']
        if 'port' in conf:
            self.port = conf['port']
        if 'delay' in conf:
            self.delay = conf['delay']
        if 'timeout' in conf:
            self.timeout = conf['timeout']

    def probe(self):
        self.mtda.debug(3, "console.telnet.probe()")
        result = True
        self.mtda.debug(3, "console.telnet.probe(): %s" % str(result))
        return result

    def open(self):
        self.mtda.debug(3, "console.telnet.open()")

        result = self.opened
        if self.opened is False:
            try:
                self.telnet = Telnet()
                self.telnet.open(self.host, self.port, self.timeout)
                self.opened = True
                result = True
            except OSError:
                result = False

        self.mtda.debug(3, "console.telnet.open(): %s" % str(result))
        return result

    def close(self):
        self.mtda.debug(3, "console.telnet.close()")

        if self.opened is True:
            self.opened = False
            self.telnet.get_socket().shutdown(socket.SHUT_WR)
            self.telnet.close()
            self.telnet = None
        result = (self.opened is False)

        self.mtda.debug(3, "console.telnet.close(): %s" % str(result))
        return result

    """ Return number of pending bytes to read"""
    def pending(self):
        self.mtda.debug(3, "console.telnet.pending()")

        if self.opened is True:
            result = self.telnet.sock_avail()
        else:
            result = False

        self.mtda.debug(3, "console.telnet.pending(): %s" % str(result))
        return result

    """ Read bytes from the console"""
    def read(self, n=1):
        self.mtda.debug(3, "console.telnet.read(n=%d)" % n)

        if self.opened is False:
            time_before_open = time.time()
            self.open()
            if self.opened is False:
                # make sure we do not return too quickly
                # if we could not connect
                self.mtda.debug(4, "console.telnet.read():"
                                " failed to connnect!")
                time_after_open = time.time()
                elapsed_time = time_after_open - time_before_open
                if elapsed_time < self.delay:
                    delay = self.delay - elapsed_time
                    self.mtda.debug(4, "console.telnet.read():"
                                    " sleeping {0} seconds".format(delay))
                    time.sleep(delay)

        data = bytearray()
        try:
            while n > 0 and self.opened is True:
                avail = self.telnet.read_some()
                data = data + avail
                n = n - len(avail)
        except socket.timeout:
            self.mtda.debug(2, "console.telnet.read(): timeout!")

        self.mtda.debug(3, "console.telnet.read(): %d bytes" % len(data))
        return data

    """ Write to the console"""
    def write(self, data):
        self.mtda.debug(3, "console.telnet.write()")

        if self.opened is True:
            result = self.telnet.write(data)
        else:
            self.mtda.debug(2, "console.telnet.write(): not connected!")
            result = None

        self.mtda.debug(3, "console.telnet.write(): %s" % str(result))
        return result


def instantiate(mtda):
    return TelnetConsole(mtda)
