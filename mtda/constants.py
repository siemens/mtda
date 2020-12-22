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


class IMAGE(Enum):
    RAW = 0
    BZ2 = 1
    GZ = 2
    ZST = 3


class RPC:
    TIMEOUT = 2*60


class WRITER:
    QUEUE_SLOTS = 16
    QUEUE_TIMEOUT = 5
    READ_SIZE = 1*1024*1024
    WRITE_SIZE = 1*1024*1024
