# ---------------------------------------------------------------------------
# common things for our tests
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import re


class Consts:
    # Timeouts (in seconds)
    BOOT_TIMEOUT = 5*60
    PASSWORD_TIMEOUT = 30
    PROMPT_TIMEOUT = 30


class Utils:
    def escape_ansi(line):
        ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', str(line))
