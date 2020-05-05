# System imports
import abc
import serial

# Local imports
from mtda.console.interface import ConsoleInterface

class SerialConsole(ConsoleInterface):

    def __init__(self):
        self.ser  = None
        self.port = "/dev/ttyUSB0"
        self.rate = 115200
        self.opened = False

    def configure(self, conf):
        """ Configure this console from the provided configuration"""
        if 'port' in conf:
            self.port = conf['port']
        if 'rate' in conf:
            self.rate = int(conf['rate'], 10)
        self.ser = serial.Serial()
        self.ser.port = self.port
        self.ser.baudrate = self.rate

    def probe(self):
        if self.ser is not None:
            if self.opened == False:
                self.ser.open()
                self.opened = True
            return self.opened
        else:
            return False

    def close(self):
        if self.ser is not None:
            if self.opened == False:
                self.ser.close()
                self.opened = False

    def pending(self):
        """ Return number of pending bytes to read"""
        if self.ser is not None:
            return self.ser.inWaiting()
        else:
            return 0

    def read(self, n=1):
        """ Read bytes from the console"""
        if self.ser is not None:
            return self.ser.read(n)
        else:
            return None

    def write(self, data):
        """ Write to the console"""
        if self.ser is not None:
            return self.ser.write(data)
        else:
            return None

def instantiate():
    return SerialConsole()
