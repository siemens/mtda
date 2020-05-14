# System imports
import abc

# Local imports
from mtda.usb.switch import UsbSwitch

class GpioUsbSwitch(UsbSwitch):

    def __init__(self):
        self.dev     = None
        self.pin     = 0
        self.enable  = 1
        self.disable = 0

    def configure(self, conf):
        """ Configure this USB switch from the provided configuration"""
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
        return

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
        """ Power on the target USB port"""
        f = open("/sys/class/gpio/gpio%d/value" % self.pin, "w")
        f.write("%d" % self.enable)
        f.close()
        return self.status() == self.POWERED_ON

    def off(self):
        """ Power off the target USB port"""
        f = open("/sys/class/gpio/gpio%d/value" % self.pin, "w")
        f.write("%d" % self.disable)
        f.close()
        return self.status() == self.POWERED_OFF

    def status(self):
        """ Determine the current power state of the USB port"""
        f = open("/sys/class/gpio/gpio%d/value" % self.pin, "r")
        value = f.read().strip()
        f.close()
        if value == self.enable:
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
   return GpioUsbSwitch()
