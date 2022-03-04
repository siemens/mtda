# ---------------------------------------------------------------------------
# GPIO power driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import os

# Local imports
from mtda.power.controller import PowerController


class GpioPowerController(PowerController):

    def __init__(self, mtda):
        self.dev = None
        self.mtda = mtda
        self.pins = []

    def configure(self, conf):
        self.mtda.debug(3, "power.gpio.configure()")

        result = None
        if 'pin' in conf:
            self.pins = [int(conf['pin'], 10)]
        if 'pins' in conf:
            self.pins = []
            values = conf['pins'].split(',')
            for v in values:
                self.pins.append(int(v, 10))

        self.mtda.debug(3, "power.gpio.configure(): {}".format(result))
        return result

    def probe(self):
        self.mtda.debug(3, "power.gpio.probe()")

        result = False
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
            result = True

        self.mtda.debug(3, "power.gpio.probe(): {}".format(result))
        return result

    def command(self, args):
        self.mtda.debug(3, "power.gpio.command()")

        result = False

        self.mtda.debug(3, "power.gpio.command(): {}".format(result))
        return result

    def on(self):
        self.mtda.debug(3, "power.gpio.on()")

        result = False
        for pin in self.pins:
            f = open("/sys/class/gpio/gpio%d/value" % pin, "w")
            f.write("1")
            f.close()
        result = self.status() == self.POWER_ON

        self.mtda.debug(3, "power.gpio.on(): {}".format(result))
        return result

    def off(self):
        self.mtda.debug(3, "power.gpio.off()")

        result = False
        for pin in self.pins:
            f = open("/sys/class/gpio/gpio%d/value" % pin, "w")
            f.write("0")
            f.close()
        result = self.status() == self.POWER_OFF

        self.mtda.debug(3, "power.gpio.off(): {}".format(result))
        return result

    def status(self):
        self.mtda.debug(3, "power.gpio.status()")

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
            self.mtda.debug(3, "power.gpio.status: "
                               "pin #%d is %s" % (pin, value))
            if first is True:
                first = False
                result = value
            elif value != result:
                result = self.POWER_UNSURE

        self.mtda.debug(3, "power.gpio.status(): {}".format(result))
        return result

    def toggle(self):
        """ Toggle power for the attached device"""
        s = self.status()
        if s == self.POWER_OFF:
            self.on()
        else:
            self.off()
        return self.status()


def instantiate(mtda):
    return GpioPowerController(mtda)
