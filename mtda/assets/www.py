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

import asyncio
import json
import uuid

from pyodide.http import pyfetch
from urllib.parse import urlencode

# ---------------------------------------------------------------------------
# Helpers for the interpreter
# ---------------------------------------------------------------------------


def get_completions(text):
    completions = []
    for key in globals().keys():
        if key.startswith(text):
            completions.append(key)
    return json.dumps(completions)

# ---------------------------------------------------------------------------
# Implement our Python APIs using REST endpoints
# ---------------------------------------------------------------------------


PY_SESSION_ID = uuid.uuid4()


class Storage:
    async def toggle():
        """
        Toggle the shared storage between the HOST and TARGET

        Returns:
            str: the new state ("HOST", "TARGET" or "???")
        """
        response = await Support.get_data("/storage-toggle",
                                          {"session": PY_SESSION_ID})
        if 'result' in response:
            return response['result']['status']
        return '???'


class Support:
    async def get_data(endpoint, params=None):
        if params:
            query = urlencode(params)
            endpoint = f"{endpoint}?{query}"
        response = await pyfetch(endpoint, method="GET")
        return await response.json()


class Target:
    async def toggle():
        """
        Toggle the power state of the target.

        Returns:
            str: the new state ("ON", "OFF" or "???")
        """
        response = await Support.get_data("/power-toggle",
                                          {"session": PY_SESSION_ID})
        if 'result' in response:
            return response['result']['status']
        return '???'
