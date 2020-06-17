# System imports
import abc
import os

# Local imports
from mtda.usb.switch import UsbSwitch

class GpioUsbSwitch(UsbSwitch):

    def __init__(self, mtda):
        self.dev     = None
        self.pin     = 0
        self.enable  = 1
        self.disable = 0
        self.mtda    = mtda

    def configure(self, conf):
        """ Configure this USB switch from the provided configuration"""
        self.mtda.debug(3, "usb.gpio.configure()")
        if 'pin' in conf:
            self.pin = int(conf['pin'], 10)
        if 'enable' in conf:
            if conf['enable'] == 'high':
                self.enable  = 1
                self.disable = 0
            elif conf['enable'] == 'low':
                self.enable  = 0
                self.disable = 1
            else:
                raise ValueError("'enable' shall be either 'high' or 'low'!")

        result = True
        self.mtda.debug(3, "usb.gpio.configure(): %s" % str(result))
        return result

    def probe(self):
        self.mtda.debug(3, "usb.gpio.probe()")
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

        result = True
        self.mtda.debug(3, "usb.gpio.probe(): %s" % str(result))
        return result

    def on(self):
        """ Power on the target USB port"""
        self.mtda.debug(3, "usb.gpio.on()")
        f = open("/sys/class/gpio/gpio%d/value" % self.pin, "w")
        f.write("%d" % self.enable)
        f.close()
        result = self.status() == self.POWERED_ON
        self.mtda.debug(3, "usb.gpio.on(): %s" % str(result))
        return result

    def off(self):
        """ Power off the target USB port"""
        self.mtda.debug(3, "usb.gpio.off()")
        f = open("/sys/class/gpio/gpio%d/value" % self.pin, "w")
        f.write("%d" % self.disable)
        f.close()
        result = self.status() == self.POWERED_OFF
        self.mtda.debug(3, "usb.gpio.off(): %s" % str(result))
        return result

    def status(self):
        """ Determine the current power state of the USB port"""
        self.mtda.debug(3, "usb.gpio.status()")
        f = open("/sys/class/gpio/gpio%d/value" % self.pin, "r")
        value = f.read().strip()
        f.close()
        if value == str(self.enable):
            result = self.POWERED_ON
        else:
            result = self.POWERED_OFF

        self.mtda.debug(3, "usb.gpio.status(): %s" % str(result))
        return result

    def toggle(self):
        self.mtda.debug(3, "usb.gpio.toggle()")
        s = self.status()
        if s == self.POWERED_ON:
            self.off()
            result = self.POWERED_OFF
        else:
            self.on()
            result = self.POWERED_ON

        self.mtda.debug(3, "usb.gpio.toggle(): %s" % str(result))
        return result

def instantiate(mtda):
   return GpioUsbSwitch(mtda)
