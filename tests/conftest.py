# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2023 Siemens Digital Industries Software
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
