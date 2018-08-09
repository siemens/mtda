# System imports
import abc
import RPi.GPIO as GPIO

# Local imports
from mtda.usb.switch import UsbSwitch

class RPiGpioUsbSwitch(UsbSwitch):

    def __init__(self):
        self.dev     = None
        self.pin     = 0
        self.enable  = GPIO.HIGH
        self.disable = GPIO.LOW
        GPIO.setwarnings(False)

    def configure(self, conf):
        """ Configure this USB switch from the provided configuration"""
        if 'pin' in conf:
            self.pin = int(conf['pin'], 10)
        if 'enable' in conf:
            if conf['enable'] == 'high':
                self.enable  = GPIO.HIGH
                self.disable = GPIO.LOW
            elif conf['enable'] == 'low':
                self.enable  = GPIO.LOW
                self.disable = GPIO.HIGH
        if self.pin > 0:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)
        return

    def probe(self):
        return

    def on(self):
        """ Power on the target USB port"""
        GPIO.output(self.pin, self.enable)
        return self.status() == self.POWERED_ON

    def off(self):
        """ Power off the target USB port"""
        GPIO.output(self.pin, self.disable)
        return self.status() == self.POWERED_OFF

    def status(self):
        """ Determine the current power state of the USB port"""
        if GPIO.input(self.pin) == self.enable:
            return self.POWERED_ON
        else:
            return self.POWERED_OFF

    def toggle(self):
        s = self.status()
        if s == self.POWERED_ON:
            self.off()
            return self.POWERED_OFF
        else:
            self.on()
            return self.POWERED_ON

def instantiate():
   return RPiGpioUsbSwitch()
