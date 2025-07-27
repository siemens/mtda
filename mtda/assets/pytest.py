# ---------------------------------------------------------------------------
# pytest support from the browser
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import asyncio
import mtda.asyncio

# ---------------------------------------------------------------------------
# Implement our Python APIs using REST endpoints
# ---------------------------------------------------------------------------


class Test:
    @staticmethod
    def init():
        return mtda.asyncio.Test.init()

    @staticmethod
    def initialized():
        return mtda.asyncio.Test.initialized()

    @staticmethod
    def setup():
        assert Test.init() is True
        return Console.clear()

    @staticmethod
    def sleep(seconds):
        assert Test.initialized() is True
        return Support.call(asyncio.sleep(seconds))

    @staticmethod
    def teardown():
        assert Test.initialized() is True
        return Console.clear()


class Console:
    @staticmethod
    def clear():
        return Support.call(mtda.asyncio.Console.clear())

    @staticmethod
    def dump():
        return Support.call(mtda.asyncio.Console.dump())

    @staticmethod
    def flush():
        return Support.call(mtda.asyncio.Console.flush())

    @staticmethod
    def head():
        return Support.call(mtda.asyncio.Console.head())

    @staticmethod
    def lines():
        return Support.call(mtda.asyncio.Console.lines())

    @staticmethod
    def send(what):
        return Support.call(mtda.asyncio.Console.send(what))

    @staticmethod
    def tail():
        return Support.call(mtda.asyncio.Console.tail())

    @staticmethod
    def wait_for(what, errors=None, timeout=30, intervals=5,
                 screen="", flush=True):
        return Support.call(mtda.asyncio.Console.wait_for(what, errors, timeout,
                                                          intervals, screen,
                                                          flush))


class Storage:
    def commit():
        return Support.call(mtda.asyncio.Storage.commit())

    def rollback():
        return Support.call(mtda.asyncio.Storage.rollback())

    def toggle():
        return Support.call(mtda.asyncio.Storage.toggle())

    def to_host():
        return Support.call(mtda.asyncio.Storage.to_host())

    def to_target():
        return Support.call(mtda.asyncio.Storage.to_target())


class Support:
    @staticmethod
    def call(fn):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(fn)


class Target:
    @staticmethod
    def off():
        return Support.call(mtda.asyncio.Target.off())

    @staticmethod
    def on():
        return Support.call(mtda.asyncio.Target.on())

    @staticmethod
    def status():
        return Support.call(mtda.asyncio.Target.status())

    @staticmethod
    def toggle():
        return Support.call(mtda.asyncio.Target.toggle())

    @staticmethod
    def uptime():
        return Support.call(mtda.asyncio.Target.uptime())
