# ---------------------------------------------------------------------------
# GPIO usb driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2024 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import gpiod
from operator import itemgetter

# Local imports
from mtda.usb.switch import UsbSwitch


class GpioUsbSwitch(UsbSwitch):

    def __init__(self, mtda):
        self.dev = None
        self.pin = 0
        self.enable = 1
        self.disable = 0
        self.mtda = mtda
        self.lines = []
        self.gpiopair = []

    def configure(self, conf):
        """ Configure this USB switch from the provided configuration"""
        self.mtda.debug(3, "usb.gpio.configure()")
        if 'pin' in conf:
            self.pin = int(conf['pin'], 10)
        if 'enable' in conf:
            if conf['enable'] == 'high':
                self.enable = 1
                self.disable = 0
            elif conf['enable'] == 'low':
                self.enable = 0
                self.disable = 1
            else:
                raise ValueError("'enable' shall be either 'high' or 'low'!")
        if 'gpio' in conf:
            for gpio in conf['gpio'].split(','):
                self.gpiopair.append(itemgetter(0, 1)(gpio.split('@')))

        result = True
        self.mtda.debug(3, f"usb.gpio.configure(): {str(result)}")
        return result

    def probe(self):
        self.mtda.debug(3, "usb.gpio.probe()")
        if not self.gpiopair:
            raise ValueError("GPIO chip(s) and pin(s) pair not configured")

        for chip, pin in self.gpiopair:
            pin = int(pin)
            chip = gpiod.Chip(chip, gpiod.Chip.OPEN_BY_NAME)
            self.mtda.debug(3, "this is chip {} and pin is {} "
                               "power.gpio.configure(): ".format(chip, pin))
            self.lines.append(chip.get_line(pin))

        for line in self.lines:
            try:
                if line.is_used() is False:
                    self.mtda.debug(3, f"power.gpiochip{chip}@pin{pin} "
                                       "is free for use")
                    line.request(consumer='mtda', type=gpiod.LINE_REQ_DIR_OUT)
                else:
                    raise ValueError("gpiochip{}@pin{} is in use by other "
                                     "service" .format(chip, pin))
            except OSError:
                self.mtda.debug(3, f"line {line} is not configured correctly")

        result = True
        self.mtda.debug(3, f"usb.gpio.probe(): {result}")
        return result

    def on(self):
        """ Power on the target USB port"""
        self.mtda.debug(3, "usb.gpio.on()")
        for line in self.lines:
            line.set_value(self.enable)
        result = self.status() == self.POWERED_ON
        self.mtda.debug(3, f"usb.gpio.on(): {result}")
        return result

    def off(self):
        """ Power off the target USB port"""
        self.mtda.debug(3, "usb.gpio.off()")
        for line in self.lines:
            line.set_value(self.disable)
        result = self.status() == self.POWERED_OFF
        self.mtda.debug(3, f"usb.gpio.off(): {result}")
        return result

    def status(self):
        """ Determine the current power state of the USB port"""
        self.mtda.debug(3, "usb.gpio.status()")
        value = self.line.get_value()
        for line in self.lines:
            value = line.get_value()
            if value == self.enable:
                result = self.POWERED_ON
            else:
                result = self.POWERED_OFF

            self.mtda.debug(3, f"usb.gpio.status():line {line} is {value}")
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

        self.mtda.debug(3, f"usb.gpio.toggle(): {str(result)}")
        return result


def instantiate(mtda):
    return GpioUsbSwitch(mtda)
