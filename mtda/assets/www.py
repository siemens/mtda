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


def get_completions(text):
    import json
    completions = []
    for key in globals().keys():
        if key.startswith(text):
            completions.append(key)
    return json.dumps(completions)


def init_user_workspace():
    import os
    import shutil
    if os.path.exists("/user"):
        shutil.rmtree("/user")
    os.mkdir("/user")


def www_init():
    import sys
    sys.path.insert(0, "/opt")


www_init()
del www_init
