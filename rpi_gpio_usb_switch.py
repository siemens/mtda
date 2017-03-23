# System imports
import abc
import RPi.GPIO as GPIO

# Local imports
from usb_switch import UsbSwitch

class RPiGpioUsbSwitch(UsbSwitch):

    def __init__(self):
        self.dev = None
        self.pin = 0
        GPIO.setwarnings(False)

    def configure(self, conf):
        """ Configure this USB switch from the provided configuration"""
        if 'pin' in conf:
            self.pin = int(conf['pin'], 10)
        if self.pin > 0:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)
        return

    def probe(self):
        return

    def on(self):
        """ Power on the target USB port"""
        return GPIO.output(self.pin, GPIO.HIGH)

    def off(self):
        """ Power off the target USB port"""
        return GPIO.output(self.pin, GPIO.LOW)

    def status(self):
        """ Determine the current power state of the USB port"""
        return POWERED_OFF

def instantiate():
   return RPiGpioUsbSwitch()
