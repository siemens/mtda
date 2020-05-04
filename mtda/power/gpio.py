# System imports
import abc
import os
import threading

# Local imports
from mtda.power.controller import PowerController

class GpioPowerController(PowerController):

    def __init__(self):
        self.dev = None
        self.ev  = threading.Event()
        self.pin = None

    def configure(self, conf):
        """ Configure this power controller from the provided configuration"""
        if 'pin' in conf:
           self.pin = int(conf['pin'], 10)

    def probe(self):
        if self.pin is None:
            raise ValueError("GPIO pin not configured!")

        if os.path.islink("/sys/class/gpio/gpio%d" % self.pin) == False:
            f = open("/sys/class/gpio/export", "w")
            f.write("%d" % self.pin)
            f.close()

        if os.path.islink("/sys/class/gpio/gpio%d" % self.pin) == False:
            raise ValueError("GPIO %d not found in sysfs!" % self.pin)

        f = open("/sys/class/gpio/gpio%d/direction" % self.pin, "w")
        f.write("out")
        f.close()

    def on(self):
        """ Power on the attached device"""
        f = open("/sys/class/gpio/gpio%d/value" % self.pin, "w")
        f.write("1")
        f.close()
        status = self.status()
        if status == self.POWER_ON:
            self.ev.set()
            return True
        return False

    def off(self):
        """ Power off the attached device"""
        f = open("/sys/class/gpio/gpio%d/value" % self.pin, "w")
        f.write("0")
        f.close()
        status = self.status()
        if status == self.POWER_OFF:
            self.ev.set()
            return True
        return False

    def status(self):
        """ Determine the current power state of the attached device"""
        f = open("/sys/class/gpio/gpio%d/value" % self.pin, "r")
        value = f.read().strip()
        f.close()
        if value == '1':
            return self.POWER_ON
        return self.POWER_OFF

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
   return GpioPowerController()
