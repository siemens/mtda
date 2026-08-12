# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2026 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------


class RetryException(Exception):
    pass


class MissingCowDeviceError(FileNotFoundError):
    """
    A operation on a cow device was requested, but
    none was configured.
    """
    def __init__(self, operation):
        super().__init__(f'{operation} failed: no CoW device was configured!')
