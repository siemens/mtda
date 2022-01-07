# ---------------------------------------------------------------------------
# Test console functions
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
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
        lines = Console.lines()
        time.sleep(1)
    assert lines > 0


def test_console_wait_for(powered_off):
    # Power on and wait for login prompt
    assert Target.on() is True
    assert Console.wait_for("login:",
                            timeout=Consts.BOOT_TIMEOUT) is not None


def test_console_head(logged_in):
    cmd = "uname -s\r\n"
    Console.send(cmd)
    time.sleep(1)
    assert Console.head().strip() == cmd.strip()


def test_console_tail(logged_in):
    prompt = "shell$ "
    Console.send("export PS1='{}'\r\n".format(prompt))
    time.sleep(1)
    assert Utils.escape_ansi(Console.tail()).strip() == prompt.strip()
