# System imports
import abc
from telnetlib import Telnet

# Local imports
from mtda.console.interface import ConsoleInterface

class TelnetConsole(ConsoleInterface):

    def __init__(self):
        self.telnet = None
        self.host = "localhost"
        self.port = 23

    def configure(self, conf):
        """ Configure this console from the provided configuration"""
        if 'host' in conf:
            self.host = conf['host']
        if 'port' in conf:
            self.port = conf['port']
        self.telnet = Telnet()

    def probe(self):
        if self.telnet is not None:
            return self.telnet.open(self.host, self.port)
        else:
            return False

    def pending(self):
        """ Return number of pending bytes to read"""
        if self.telnet is not None:
            return self.telnet.sock_avail()
        else:
            return 0

    def read(self, n=1):
        """ Read bytes from the console"""
        if self.telnet is not None:
            data = bytearray()
            while n > 0:
                avail = self.telnet.read_some()
                data = data + avail
                n = n - len(avail)
            return data
        else:
            return None

    def write(self, data):
        """ Write to the console"""
        if self.telnet is not None:
            return self.telnet.write(data)
        else:
            return None

def instantiate():
    return TelnetConsole()

