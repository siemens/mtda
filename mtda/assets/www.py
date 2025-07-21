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
import re
import uuid

from pyodide.http import pyfetch
from urllib.parse import quote

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


class Console:
    @staticmethod
    async def clear():
        """
        Clear the consle ring buffer

        Returns:
            bool: True if the request was successful
        """
        response = await Support.get("/console-clear",
                                     {"session": PY_SESSION_ID})
        return response.ok

    @staticmethod
    async def dump():
        """
        Dump contents of the console ring-buffer

        Returns:
            str: contents of the ring buffer
        """
        response = await Support.get_data("/console-dump",
                                          {"session": PY_SESSION_ID})
        if 'result' in response:
            return response['result']['content']
        return None

    @staticmethod
    async def flush():
        """
        Flush contents of the console ring-buffer

        Returns:
            str: contents of the ring buffer before it was cleared
        """
        response = await Support.get_data("/console-flush",
                                          {"session": PY_SESSION_ID})
        if 'result' in response:
            return response['result']['content']
        return None

    @staticmethod
    async def head():
        """
        Pop the first line from the console ring-buffer

        Returns:
            str: first line of the console ring buffer
        """
        response = await Support.get_data("/console-head",
                                          {"session": PY_SESSION_ID})
        if 'result' in response:
            return response['result']['content']
        return None

    @staticmethod
    async def lines():
        """
        Get the number of lines available in console ring-buffer

        Returns:
            int: count of lines available in the console ring buffer
        """
        response = await Support.get_data("/console-lines",
                                          {"session": PY_SESSION_ID})
        if 'result' in response:
            return int(response['result']['count'])
        return None

    @staticmethod
    async def send(what):
        """
        Send text to the console

        Parameters:
            str: text to send

        Returns:
            bool: True if the request was successful
        """
        response = await Support.get("/console-send",
                                     {"what": what,
                                      "session": PY_SESSION_ID})
        return response.ok

    @staticmethod
    async def tail():
        """
        Pop the last line from the console ring-buffer and remove others

        Returns:
            str: last line of the console ring buffer
        """
        response = await Support.get_data("/console-tail",
                                          {"session": PY_SESSION_ID})
        if 'result' in response:
            return response['result']['content']
        return None

    @staticmethod
    async def wait_for(what, errors=None, timeout=30, intervals=5,
                       screen="", flush=True):
        if isinstance(what, list) is False:
            what = [what]

        contents = screen
        result = None

        err_list = []
        if errors:
            if isinstance(errors, list) is False:
                errors = [errors]
            for expr in errors:
                err_list.append(re.compile(expr))

        exp_list = []
        for expr in what:
            exp_list.append(re.compile(expr))

        while timeout > 0:
            await asyncio.sleep(intervals)
            if flush is True:
                contents += await Console.flush()
            else:
                contents = screen + await Console.dump()
            # Check for errors
            for expr in err_list:
                if expr.search(contents):
                    break
            # Check for expected messages
            for expr in exp_list:
                if expr.search(contents):
                    result = contents
                    break
            if result is not None:
                break
            timeout -= intervals
        return result


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
    @staticmethod
    def sanitize_params(params):
        return {k: quote(str(v), safe='') for k, v in params.items()}

    @staticmethod
    async def get(endpoint, params=None):
        if params:
            safe_params = Support.sanitize_params(params)
            query = "&".join(f"{k}={v}" for k, v in safe_params.items())
            endpoint = f"{endpoint}?{query}"
        return await pyfetch(endpoint, method="GET")

    @staticmethod
    async def get_data(endpoint, params=None):
        response = await Support.get(endpoint, params)
        return await response.json()


class Target:
    @staticmethod
    async def off():
        """
        Power OFF the target device

        Returns:
            bool: True if the request was successful
        """
        response = await Support.get("/target-off",
                                     {"session": PY_SESSION_ID})
        return response.ok

    @staticmethod
    async def on():
        """
        Power ON the target device

        Returns:
            bool: True if the request was successful
        """
        response = await Support.get("/target-on",
                                     {"session": PY_SESSION_ID})
        return response.ok

    @staticmethod
    async def status():
        """
        Query status of the target devide ("ON" or "OFF")

        Returns:
            str: the current state ("ON", "OFF" or "???")
        """
        response = await Support.get_data("/target-status",
                                          {"session": PY_SESSION_ID})
        if 'result' in response:
            return response['result']['status']
        return '???'

    @staticmethod
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

    @staticmethod
    async def uptime():
        """
        Query uptime of the target devide (in seconds)

        Returns:
            float: seconds since the target device was powered ON
        """
        response = await Support.get_data("/target-uptime",
                                          {"session": PY_SESSION_ID})
        if 'result' in response:
            return float(response['result']['uptime'])
        return None
