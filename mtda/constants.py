# ---------------------------------------------------------------------------
# MTDA Constants
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
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
    WWW_WORKERS = 10
    IMAGE_FILESIZE = 8*1024**3


class EVENTS:
    INTERVAL = 30
    POWER = "POWER"
    SESSION = "SESSION"
    STORAGE = "STORAGE"
    SYSTEM = "SYSTEM"


class IMAGE(Enum):
    RAW = 0
    BZ2 = 1
    GZ = 2
    ZST = 3
    XZ = 4


class MDNS:
    TYPE = '_MTDA._tcp.local.'


class MOUSE:
    MAX_X = 32767
    MAX_Y = 32767


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
    QUEUE_LOW = "QLOW"
    QUEUE_HIGH = "QHIGH"
    ON_HOST = "HOST"
    ON_NETWORK = "NETWORK"
    ON_TARGET = "TARGET"
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"
    OPENED = "OPENED"
    WRITING = "WRITING"
    CORRUPTED = "CORRUPTED"
    INITIALIZED = "INITIALIZED"
    UNKNOWN = "???"
    RETRY_INTERVAL = 0.5
    TIMEOUT = 30


class USB:
    HID_KEYBOARD = "/dev/mtda-hid-keyboard"
    HID_MOUSE = "/dev/mtda-hid-mouse"


class WRITER:
    HIGH_WATER_MARK = 16*1024**2
    RECV_RETRIES = 5
    RECV_TIMEOUT = 5
    SEND_BACKOFF_BASE = 0.1
    SEND_MAX_WAIT = 10
    READ_SIZE = 512*1024
    WRITE_SIZE = 512*1024
    NOTIFY_SECONDS = 1
