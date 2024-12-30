# ---------------------------------------------------------------------------
# Test config functions
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import time

import mtda.constants as CONSTS

from mtda.pytest import Config
from mtda.pytest import Target


def test_config_set_power_timeout(powered_off):
    # Make sessions expire quickly for this test
    Config.set_session_timeout(10)

    # Check with a power timeout of 1 minute
    Config.set_power_timeout(60)
    assert Target.on() is True
    time.sleep(20)
    assert Target.status() == CONSTS.POWER.ON
    time.sleep(20)
    assert Target.status() == CONSTS.POWER.ON
    time.sleep(60)
    assert Target.status() == CONSTS.POWER.OFF

    # Check with a power timeout of 30 seconds
    Config.set_power_timeout(30)
    assert Target.on() is True
    time.sleep(10)
    assert Target.status() == CONSTS.POWER.ON
    time.sleep(10)
    assert Target.status() == CONSTS.POWER.ON
    time.sleep(30)
    assert Target.status() == CONSTS.POWER.OFF

    # Check with power timeout disabled
    Config.set_power_timeout(0)
    assert Target.on() is True
    time.sleep(60)
    assert Target.status() == CONSTS.POWER.ON
