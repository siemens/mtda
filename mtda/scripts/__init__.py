# ---------------------------------------------------------------------------
# Scripts for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2024 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import importlib
from gevent import sleep


def load_device_scripts(variant, env):
    try:
        scripts = importlib.import_module("mtda.scripts." + variant)
        for op in ops.keys():
            name = f"{variant}_{op.replace('-', '_')}"
            if hasattr(scripts, name) is False:
                continue
            method = getattr(scripts, name)
            if method is not None:
                ops[op][variant] = method
        for e in env.keys():
            setattr(scripts, e, env[e])
        return True
    except ImportError:
        return False


def op_handler(name):
    if name in ops and variant in ops[name]:
        mtda.debug(2, f"calling '{name}' device script")
        mtda.env_set(name, '0')
        result = ops[name][variant]()
        mtda.env_set(name, f'{result}')
    else:
        if variant != 'unknown':
            mtda.debug(1, f"no '{name}' script provided for '{variant}'")
        mtda.env_set(name, 'not supported')


def check_op_handler(name):
    if name in env and env[name] == '1':
        op_handler(name)
        return True
    else:
        return False


def check_reset_tpm():
    return check_op_handler('reset-tpm')


def check_reset_tpm_factory():
    return check_op_handler('reset-tpm-factory')


def check_disable_secureboot():
    return check_op_handler('disable-secureboot')


def check_enable_secureboot():
    return check_op_handler('enable-secureboot')


def check_boot_from_usb():
    return check_op_handler('boot-from-usb')


def power_on():
    return op_handler('power-on')


def power_off():
    return op_handler('power-off')

# ---------------------------------------------------------------------------
# Dictionary of supported operations
# ---------------------------------------------------------------------------


ops = {
    'boot-from-usb': {},
    'disable-secureboot': {},
    'enable-secureboot': {},
    'power-on': {},
    'reset-tpm': {},
    'reset-tpm-factory': {}
}
