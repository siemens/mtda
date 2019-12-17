# System imports
import abc
import socket
import time
from telnetlib import Telnet

# Local imports
from mtda.console.interface import ConsoleInterface

class TelnetConsole(ConsoleInterface):

    def __init__(self):
        self.telnet = None
        self.host = "localhost"
        self.port = 23
        self.opened = False
        self.delay = 5

    def configure(self, conf):
        """ Configure this console from the provided configuration"""
        if 'host' in conf:
            self.host = conf['host']
        if 'port' in conf:
            self.port = conf['port']
        if 'delay' in conf:
            self.delay = conf['delay']

    def probe(self):
        result = False
        if self.opened == False:
            try:
                self.telnet = Telnet()
                self.telnet.open(self.host, self.port)
                self.opened = True
                result = True
            except OSError:
                pass
        return result

    def close(self):
        if self.opened == True:
            self.opened = False
            self.telnet.get_socket().shutdown(socket.SHUT_WR)
            self.telnet.close()
            self.telnet = None

    def pending(self):
        """ Return number of pending bytes to read"""
        if self.opened == True:
            return self.telnet.sock_avail()
        else:
            return 0

    def read(self, n=1):
        """ Read bytes from the console"""
        if self.opened == False:
            time_before_probe = time.time()
            self.probe()
            # make sure we do not return too quickly if we could not connect
            time_after_probe = time.time()
            elapsed_time = time_after_probe - time_before_probe
            if elapsed_time < self.delay:
                time.sleep(self.delay - elapsed_time)
        data = bytearray()
        while n > 0 and self.opened == True:
            avail = self.telnet.read_some()
            data = data + avail
            n = n - len(avail)
        return data

    def write(self, data):
        """ Write to the console"""
        if self.opened == True:
            return self.telnet.write(data)
        else:
            return None

def instantiate():
    return TelnetConsole()

