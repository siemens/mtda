# ---------------------------------------------------------------------------
# GPIO power driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (c) Mentor, a Siemens business, 2017-2020
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import abc
import os
import threading

# Local imports
from mtda.power.controller import PowerController


class GpioPowerController(PowerController):

    def __init__(self, mtda):
        self.dev = None
        self.ev = threading.Event()
        self.mtda = mtda
        self.pins = []

    def configure(self, conf):
        """ Configure this power controller from the provided configuration"""
        if 'pin' in conf:
            self.pins = [int(conf['pin'], 10)]
        if 'pins' in conf:
            self.pins = []
            values = conf['pins'].split(',')
            for v in values:
                self.pins.append(int(v, 10))

    def probe(self):
        if self.pins is None:
            raise ValueError("GPIO pin(s) not configured!")

        for pin in self.pins:
            if os.path.islink("/sys/class/gpio/gpio%d" % pin) is False:
                f = open("/sys/class/gpio/export", "w")
                f.write("%d" % pin)
                f.close()

            if os.path.islink("/sys/class/gpio/gpio%d" % pin) is False:
                raise ValueError("GPIO %d not found in sysfs!" % pin)

            f = open("/sys/class/gpio/gpio%d/direction" % pin, "w")
            f.write("out")
            f.close()

    def command(self, args):
        return False

    def on(self):
        """ Power on the attached device"""
        for pin in self.pins:
            f = open("/sys/class/gpio/gpio%d/value" % pin, "w")
            f.write("1")
            f.close()
        status = self.status()
        if status == self.POWER_ON:
            self.ev.set()
            return True
        return False

    def off(self):
        """ Power off the attached device"""
        for pin in self.pins:
            f = open("/sys/class/gpio/gpio%d/value" % pin, "w")
            f.write("0")
            f.close()
        status = self.status()
        if status == self.POWER_OFF:
            self.ev.clear()
            return True
        return False

    def status(self):
        """ Determine the current power state of the attached device"""
        first = True
        result = self.POWER_UNSURE
        for pin in self.pins:
            f = open("/sys/class/gpio/gpio%d/value" % pin, "r")
            value = f.read().strip()
            f.close()
            if value == '1':
                value = self.POWER_ON
            else:
                value = self.POWER_OFF
            self.mtda.debug(3, "power.gpio.status: pin #%d is %s" % (pin, value))
            if first is True:
                first = False
                result = value
            elif value != result:
                result = self.POWER_UNSURE
        return result

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


def instantiate(mtda):
    return GpioPowerController(mtda)
