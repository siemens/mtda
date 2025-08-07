# ---------------------------------------------------------------------------
# Helper classes for writing pytest units
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import os
import pytest
import re
import sys
import threading
import time

import mtda.client
import mtda.constants as CONSTS
from mtda.console.screen import ScreenOutput

pytest.mtda = None


class Test:
    def init():
        if pytest.mtda is not None:
            return True

        # Initialize client
        pytest.logging = False
        pytest.mtda = mtda.client.Client()
        pytest.output = TestOutput()
        remote = pytest.mtda.remote()
        pytest.mtda.console_remote(remote, pytest.output)
        pytest.mtda.monitor_remote(remote, pytest.output)
        pytest.mtda.start()

        # Start test-suite with the DUT powered off
        assert Target.off() is True

        # Initialize boot media
        image = os.getenv("TEST_IMAGE", Consts.DEFAULT_IMAGE)
        if os.path.exists(image) is False:
            if image != Consts.DEFAULT_IMAGE:
                return False
            else:
                image = ""

        if image:
            Storage.to_host()
            Storage.write(image)
            Storage.to_target()
            Env.set("boot-from-usb", "1")

        return True

    def initialized():
        return pytest.mtda is not None

    def setup():
        assert Test.init() is True

        Console.clear()
        Console.unmute()
        Config.set_power_timeout(CONSTS.DEFAULTS.POWER_TIMEOUT)
        Config.set_session_timeout(CONSTS.DEFAULTS.SESSION_TIMEOUT)

    def teardown():
        assert Test.initialized() is True

        Console.mute()
        Console.clear()


class Config:
    def set_power_timeout(timeout):
        return pytest.mtda.config_set_power_timeout(timeout)

    def set_session_timeout(timeout):
        return pytest.mtda.config_set_session_timeout(timeout)


class Consts:
    # Default image
    DEFAULT_IMAGE = "test-image.wic.img"

    # Timeouts (in seconds)
    POWER_TIMEOUT = 30


class Console:
    def clear():
        return pytest.mtda.console_clear()

    def dump():
        return pytest.mtda.console_dump()

    def flush():
        return pytest.mtda.console_flush()

    def head():
        return pytest.mtda.console_head()

    def lines():
        return pytest.mtda.console_lines()

    def mute():
        pytest.logging = False

    def send(what):
        return pytest.mtda.console_send(what)

    def tail():
        return pytest.mtda.console_tail()

    def unmute():
        pytest.logging = True

    def wait_for(what, errors=None, timeout=30, intervals=5,
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
            if flush is True:
                contents += pytest.mtda.console_flush()
            else:
                contents = screen + pytest.mtda.console_dump()
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
            time.sleep(intervals)
            timeout -= intervals
        return result


class Env:
    def set(name, value):
        return pytest.mtda.env_set(name, value)


class Storage:
    def commit():
        return pytest.mtda.storage_commit()

    def rollback():
        return pytest.mtda.storage_rollback()

    def to_host():
        return pytest.mtda.storage_to_host()

    def to_target():
        return pytest.mtda.storage_to_target()

    def write(image):
        return pytest.mtda.storage_write_image(image)


class TestOutput(ScreenOutput):
    def __init__(self):
        super().__init__(pytest.mtda)
        self._power_event = threading.Event()

    def on_event(self, event):
        # Print events to stderr
        print(event, file=sys.stderr)

        # Parse event data
        info = event.split()
        domain = info[0]

        # Check for POWER events
        if domain == "POWER" and self._power_event is not None:
            self._power_event.set()

    def clear_power(self):
        self._power_event.clear()

    def wait_power(self):
        result = self._power_event.wait(Consts.POWER_TIMEOUT)
        self._power_event.clear()
        return result

    def write(self, data):
        if pytest.logging is True:
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()


class Target:
    def off():
        pytest.output.clear_power()
        old_status = pytest.mtda.target_status()
        result = pytest.mtda.target_off()
        if result is True and old_status != "OFF":
            result = pytest.output.wait_power()
        return result

    def on():
        pytest.output.clear_power()
        old_status = pytest.mtda.target_status()
        result = pytest.mtda.target_on()
        if result is True and old_status != "ON":
            result = pytest.output.wait_power()
        return result

    def status():
        return pytest.mtda.target_status()

    def toggle():
        pytest.output.clear_power()
        result = pytest.mtda.target_toggle()
        pytest.output.wait_power()
        return result

    def uptime():
        return pytest.mtda.target_uptime()
