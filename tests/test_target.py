# ---------------------------------------------------------------------------
# Test target functions
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import requests
import time

from common import Consts
from mtda.pytest import Target


def do_target_off(off):
    assert Target.status() == "ON"
    status = off()
    assert status == 204
    assert Target.status() == "OFF"


def test_target_off(powered_on):
    def off():
        Target.off()
        return 204
    do_target_off(off)


def test_www_target_off(powered_on):
    def off():
        params = {"session": "pytest"}
        response = requests.get(f"{Consts.BASE_URL}/target-off",
                                params=params)
        return response.status_code
    do_target_off(off)


def do_target_on(on):
    assert Target.status() == "OFF"
    status = on()
    assert status == 204
    assert Target.status() == "ON"


def test_target_on(powered_off):
    def on():
        Target.on()
        return 204
    do_target_on(on)


def test_www_target_on(powered_off):
    def on():
        params = {"session": "pytest"}
        response = requests.get(f"{Consts.BASE_URL}/target-on",
                                params=params)
        return response.status_code
    do_target_on(on)


def do_target_toggle(toggle):
    assert Target.status() == "OFF"
    status, target_status = toggle()
    assert status == 200
    assert target_status == "ON"
    assert Target.status() == "ON"
    status, target_status = toggle()
    assert status == 200
    assert target_status == "OFF"
    assert Target.status() == "OFF"


def test_target_toggle(powered_off):
    def toggle():
        return 200, Target.toggle()
    do_target_toggle(toggle)


def test_www_target_toggle(powered_off):
    def toggle():
        params = {"session": "pytest"}
        response = requests.get(f"{Consts.BASE_URL}/power-toggle",
                                params=params)
        status = response.status_code
        result = response.json()["result"]["status"] if status == 200 else None
        return status, result
    do_target_toggle(toggle)

def do_target_uptime(uptime):
    status, t1 = uptime()
    assert status == 200
    assert t1 == 0
    time.sleep(3)
    status, t2 = uptime()
    assert status == 200
    assert t2 == t1
    assert Target.on() is True
    status, t3 = uptime()
    assert status == 200
    time.sleep(3)
    status, t4 = uptime()
    assert status == 200
    assert t4 > t3
    assert Target.off() is True
    status, t5 = uptime()
    assert status == 200
    assert t5 == 0


def test_target_uptime(powered_off):
    def uptime():
        return 200, Target.uptime()
    do_target_uptime(uptime)


def test_www_target_uptime(powered_off):
    def uptime():
        params = {"session": "pytest"}
        response = requests.get(f"{Consts.BASE_URL}/target-uptime",
                                params=params)
        status = response.status_code
        result = response.json()["result"]["uptime"] if status == 200 else None
        return status, result
    do_target_uptime(uptime)
