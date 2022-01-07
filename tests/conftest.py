# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import pytest
import time

from common import Consts

from mtda.pytest import Console
from mtda.pytest import Target
from mtda.pytest import Test


@pytest.fixture()
def powered_off():
    Test.setup()
    assert Target.off() is True

    yield "powered off"

    Test.teardown()


@pytest.fixture()
def powered_on():
    Test.setup()
    assert Target.on() is True

    yield "powered on"

    Test.teardown()


@pytest.fixture()
def logged_in():
    Test.setup()

    assert Target.on() is True

    Console.send("\x04")
    time.sleep(1)

    # Login
    assert Console.wait_for("login:",
                            timeout=Consts.BOOT_TIMEOUT) is not None
    Console.send("mtda\r\n")

    # Password
    assert Console.wait_for("Password",
                            timeout=Consts.PASSWORD_TIMEOUT) is not None
    Console.send("mtda\r\n")

    # Shell prompt
    assert Console.wait_for("mtda@",
                            timeout=Consts.PROMPT_TIMEOUT) is not None

    # Let test run within shell session
    yield "logged in"

    Test.teardown()

    # Logout
    Console.send("\x03")
    time.sleep(1)
    Console.send("\x04")
