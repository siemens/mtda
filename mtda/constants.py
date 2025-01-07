# ---------------------------------------------------------------------------
# MTDA Constants
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2021 Siemens Digital Industries Software
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
    WWW_HOST = '127.0.0.1'
    WWW_PORT = 5000


class EVENTS:
    POWER = "POWER"
    SESSION = "SESSION"
    STORAGE = "STORAGE"


class IMAGE(Enum):
    RAW = 0
    BZ2 = 1
    GZ = 2
    ZST = 3
    XZ = 4


class MDNS:
    TYPE = '_MTDA._tcp.local.'


class POWER:
    OFF = "OFF"
    ON = "ON"
    UNSURE = "???"
    LOCKED = "LOCKED"


class RPC:
    TIMEOUT = 2*60


class SESSION:
    MIN_TIMEOUT = 10
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    NONE = "NONE"
    RUNNING = "RUNNING"


class STORAGE:
    ON_HOST = "HOST"
    ON_NETWORK = "NETWORK"
    ON_TARGET = "TARGET"
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"
    OPENED = "OPENED"
    CORRUPTED = "CORRUPTED"
    UNKNOWN = "???"
    RETRY_INTERVAL = 0.5
    TIMEOUT = 30


class WRITER:
    QUEUE_SLOTS = 16
    QUEUE_TIMEOUT = 5
    READ_SIZE = 1*1024*1024
    WRITE_SIZE = 1*1024*1024
