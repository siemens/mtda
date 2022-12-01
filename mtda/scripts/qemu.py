# ---------------------------------------------------------------------------
# MTDA Scripts for QEMU
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------


def qemu_boot_from_usb():
    target = "QEMU USB"
    for i in range(60):
        sleep(0.5)
        mtda.console_send('\x1b')
        mtda.console_print('.')
        output = mtda.console_flush()
        if "Boot Manager" in output:
            break
    if "Boot Manager" in output:
        mtda.debug(1, "Entering Boot Manager")
        mtda.console_send('\x1b[B\x1b[B\r')
        sleep(1)
        output = ""
        tries = 10
        mtda.console_clear()
        while target not in output and tries > 0:
            mtda.console_send('\x1b[B')
            sleep(0.5)
            output = mtda.console_flush()
            tries = tries - 1
        if tries > 0:
            mtda.console_send('\r')


def qemu_power_on():
    scripts.check_boot_from_usb()
