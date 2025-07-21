# ---------------------------------------------------------------------------
# Python code loaded into the www Python interpreter
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import sys
import json


def get_completions(text):
    completions = []
    for key in globals().keys():
        if key.startswith(text):
            completions.append(key)
    return json.dumps(completions)
