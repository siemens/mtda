# ---------------------------------------------------------------------------
# Test console functions
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2023 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import time

from common import Consts
from common import Utils

from mtda.pytest import Console
from mtda.pytest import Target


def test_console_lines(powered_off):
    # console buffer should be empty
    lines = Console.lines() == 0

    # Power on and check if the console is getting any data
    assert Target.on() is True
    tries = 30
    while lines == 0 and tries > 0:
        Console.send('\x03\r')
        lines = Console.lines()
        time.sleep(1)
        tries = tries - 1
    assert lines > 0


def test_console_wait_for(powered_on):
    Console.send("uname -s\r")
    assert Console.wait_for("Linux") is not None


def test_console_head(powered_on):
    cmd = "uname -s\r"
    Console.send(cmd)
    time.sleep(1)
    assert Console.head().strip() == cmd.strip()


def test_console_tail(powered_on):
    prompt = "shell$ "
    Console.send("export PS1='{}'\r".format(prompt))
    time.sleep(1)
    assert Utils.escape_ansi(Console.tail()).strip() == prompt.strip()
