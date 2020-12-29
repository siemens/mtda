# ---------------------------------------------------------------------------
# MTDA Constants
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (c) Mentor, a Siemens business, 2017-2020
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

from enum import Enum


class CHANNEL:
    CONSOLE = b'CON'
    EVENTS = b'EVT'
    MONITOR = b'MON'


class DEFAULTS:
    LOCK_TIMEOUT = 5
    POWER_TIMEOUT = 60
    SESSION_TIMEOUT = 5


class IMAGE(Enum):
    RAW = 0
    BZ2 = 1
    GZ = 2
    ZST = 3


class RPC:
    HEARTBEAT = 20
    TIMEOUT = 2*60


class WRITER:
    QUEUE_SLOTS = 16
    QUEUE_TIMEOUT = 5
    READ_SIZE = 1*1024*1024
    WRITE_SIZE = 1*1024*1024
