# ---------------------------------------------------------------------------
# GPIO power driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import gpiod
from gpiod.line import Direction, Value
from operator import itemgetter

# Local imports
from mtda.power.controller import PowerController


GPIOD_V2 = hasattr(gpiod, "chip")


class GpioPowerController(PowerController):

    HIGH = 1
    LOW = 0

    def __init__(self, mtda):
        self.dev = None
        self.mtda = mtda
        self.lines = []
        self.gpiopair = []
        if GPIOD_V2:
            self.HIGH = Value.ACTIVE
            self.LOW = Value.INACTIVE
        self.trigger = self.HIGH
        self.reset = self.LOW

    def configure(self, conf):
        self.mtda.debug(3, "power.gpio.configure()")

        result = None

        if 'enable' in conf:
            if conf['enable'] == 'high':
                self.trigger = self.HIGH
            elif conf['enable'] == 'low':
                self.trigger = self.LOW
            else:
                raise ValueError("'enable' shall be either 'high' or 'low'!")

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

        for chipname, pin in self.gpiopair:
            pin = int(pin)
            self.mtda.debug(3, "power.gpio.probe(): "
                               f"chip {chipname} pin {pin}")
            if GPIOD_V2 is True:
                config = {
                    pin: gpiod.LineSettings(direction=Direction.OUTPUT)
                }
                line = gpiod.request_lines(f"/dev/{chipname}",
                                           consumer="mtda",
                                           config=config)
            else:
                chip = gpiod.Chip(chipname, gpiod.Chip.OPEN_BY_NAME)
                line = chip.get_line(pin)
            self.lines.append(line)

        for line in self.lines:
            try:
                if GPIOD_V2 is False:
                    if not line.is_used():
                        self.mtda.debug(3, "power.gpio line is free for use")
                        line.request(consumer='mtda',
                                     type=gpiod.LINE_REQ_DIR_OUT)
                    else:
                        raise ValueError("GPIO line is in use by another service")
            except Exception as e:
                self.mtda.debug(3, f"GPIO line request failed: {e}")

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
            if GPIOD_V2 is True:
                line.set_value(line.offsets[0], self.trigger)
            else:
                line.set_value(self.trigger)
        result = self.status() == self.POWER_ON

        self.mtda.debug(3, f"power.gpio.on(): {result}")
        return result

    def off(self):
        self.mtda.debug(3, "power.gpio.off()")

        result = False

        for line in self.lines:
            if GPIOD_V2 is True:
                line.set_value(line.offsets[0], self.reset)
            else:
                line.set_value(self.reset)
        result = self.status() == self.POWER_OFF

        self.mtda.debug(3, f"power.gpio.off(): {result}")
        return result

    def status(self):
        self.mtda.debug(3, "power.gpio.status()")

        first = True
        result = self.POWER_UNSURE

        for line in self.lines:
            if GPIOD_V2 is True:
                value = line.get_value(line.offsets[0])
            else:
                value = line.get_value()
            if value == self.trigger:
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
