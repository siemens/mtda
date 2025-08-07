# ---------------------------------------------------------------------------
# Test console functions
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import requests
import time

from common import Consts
from common import Utils

from mtda.pytest import Console
from mtda.pytest import Target


def do_console_lines(lines):
    # console buffer should be empty
    status, count = lines()
    assert status == 200
    assert count == 0

    # Power on and check if the console is getting any data
    assert Target.on() is True
    tries = 30
    while count == 0 and tries > 0:
        Console.send('\x03\r')
        status, count = lines()
        assert status == 200
        time.sleep(1)
        tries = tries - 1
    assert count > 0


def test_console_lines(powered_off):
    def lines():
        return 200, Console.lines()
    do_console_lines(lines)


def test_www_console_lines(powered_off):
    def lines():
        params = {"session": "pytest"}
        response = requests.get(f"{Consts.BASE_URL}/console-lines",
                                params=params)
        status = response.status_code
        result = response.json()["result"]["count"] if status == 200 else None
        return status, result
    do_console_lines(lines)


def test_console_wait_for(powered_on):
    Console.send("uname -s\r")
    assert Console.wait_for("Linux") is not None


def do_console_head(head):
    cmd = "uname -s\r"
    Console.send(cmd)
    time.sleep(1)
    status, line = head()
    assert status == 200
    assert line.strip() == cmd.strip()


def test_console_head(powered_on):
    def head():
        return 200, Console.head()
    do_console_head(head)


def test_www_console_head(powered_on):
    def head():
        params = {"session": "pytest"}
        response = requests.get(f"{Consts.BASE_URL}/console-head",
                                params=params)
        status = response.status_code
        result = response.json()["result"]["content"] if status == 200 else None
        return status, result
    do_console_head(head)
 

def do_console_tail(tail):
    prompt = "shell$ "
    Console.send("export PS1='{}'\r".format(prompt))
    time.sleep(1)
    status, line = tail()
    assert status == 200
    assert Utils.escape_ansi(line).strip() == prompt.strip()


def test_console_tail(powered_on):
    def tail():
        return 200, Console.tail()
    do_console_tail(tail)


def test_www_console_tail(powered_on):
    def tail():
        params = {"session": "pytest"}
        response = requests.get(f"{Consts.BASE_URL}/console-tail",
                                params=params)
        status = response.status_code
        result = response.json()["result"]["content"] if status== 200 else None
        return status, result
    do_console_tail(tail)
