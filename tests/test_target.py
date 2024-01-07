# ---------------------------------------------------------------------------
# Test target functions
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2024 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import time

from mtda.pytest import Target


def test_target_uptime(powered_off):
    t1 = Target.uptime()
    assert t1 == 0
    time.sleep(3)
    t2 = Target.uptime()
    assert t2 == t1
    assert Target.on() is True
    t3 = Target.uptime()
    time.sleep(3)
    t4 = Target.uptime()
    assert t4 > t3
    assert Target.off() is True
    t5 = Target.uptime()
    assert t5 == 0
