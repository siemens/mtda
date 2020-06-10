# System imports
import abc
import os
import threading

# Local imports
from mtda.power.controller import PowerController

class PduClientController(PowerController):

    def __init__(self):
        self.dev      = None
        self.ev       = threading.Event()
        self.daemon   = None
        self.hostname = None
        self.port     = None
        self.status   = self.POWER_UNSURE

    def configure(self, conf):
        """ Configure this power controller from the provided configuration"""
        if 'daemon' in conf:
           self.daemon = conf['daemon']
        if 'hostname' in conf:
           self.hostname = conf['hostname']
        if 'port' in conf:
           self.port = conf['port']

    def probe(self):
        if self.daemon is None:
            raise ValueError("machine running lavapdu-listen not specified ('daemon' not set)!")
        if self.hostname is None:
            raise ValueError("pdu not specified ('hostname' not set)!")
        if self.port is None:
            raise ValueError("port not specified!")

    def cmd(self, what):
        client = "/usr/bin/pduclient"
        return os.system("%s --daemon %s --hostname %s --command %s --port %s" % (client, self.daemon, self.hostname, what, self.port))

    def on(self):
        """ Power on the attached device"""
        status = self.cmd('on')
        if status == 0:
            self.status = self.POWER_ON
            self.ev.set()
            return True
        return False

    def off(self):
        """ Power off the attached device"""
        status = self.cmd('off')
        if status == 0:
            self.status = self.POWER_OFF
            self.ev.set()
            return True
        return False

    def status(self):
        """ Determine the current power state of the attached device"""
        return self.status

    def toggle(self):
        """ Toggle power for the attached device"""
        s = self.status()
        if s == self.POWER_OFF:
            self.on()
        else:
            self.off()
        return self.status()

    def wait(self):
        while self.status() != self.POWER_ON:
            self.ev.wait()

def instantiate():
   return PduClientPowerController()
