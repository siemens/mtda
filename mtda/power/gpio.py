# ---------------------------------------------------------------------------
# GPIO power driver for MTDA
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
from mtda.power.controller import PowerController


class GpioPowerController(PowerController):

    def __init__(self, mtda):
        self.dev = None
        self.mtda = mtda
        self.lines = []
        self.gpiopair = []

    def configure(self, conf):
        self.mtda.debug(3, "power.gpio.configure()")

        result = None

        if 'gpio' in conf:
            for gpio in conf['gpio'].split(','):
                self.gpiopair.append(itemgetter(0, 1)(gpio.split('@')))

        self.mtda.debug(3, f"power.gpio.configure(): {result}")
        return result

    def probe(self):
        self.mtda.debug(3, "power.gpio.probe()")

        result = False

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

        self.mtda.debug(3, f"power.gpio.probe(): {result}")
        return result

    def command(self, args):
        self.mtda.debug(3, "power.gpio.command()")

        result = False

        self.mtda.debug(3, f"power.gpio.command(): {result}")
        return result

    def on(self):
        self.mtda.debug(3, "power.gpio.on()")

        result = False

        for line in self.lines:
            line.set_value(1)
        result = self.status() == self.POWER_ON

        self.mtda.debug(3, f"power.gpio.on(): {result}")
        return result

    def off(self):
        self.mtda.debug(3, "power.gpio.off()")

        result = False

        for line in self.lines:
            line.set_value(0)
        result = self.status() == self.POWER_OFF

        self.mtda.debug(3, f"power.gpio.off(): {result}")
        return result

    def status(self):
        self.mtda.debug(3, "power.gpio.status()")

        first = True
        result = self.POWER_UNSURE

        for line in self.lines:
            value = line.get_value()
            if value == 1:
                value = self.POWER_ON
            else:
                value = self.POWER_OFF
            self.mtda.debug(3, f"power.gpio.status: line {line} is {value}")
            if first is True:
                first = False
                result = value
            elif value != result:
                result = self.POWER_UNSURE

        self.mtda.debug(3, f"power.gpio.status(): {result}")
        return result


def instantiate(mtda):
    return GpioPowerController(mtda)
