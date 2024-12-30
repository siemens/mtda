# ---------------------------------------------------------------------------
# MTDA Scripts for QEMU
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------


def qemu_bios_main_menu():
    mtda.debug(1, "Entering Main Menu")
    mtda.console_clear()
    for i in range(60):
        mtda.console_send('\x1b')
        mtda.console_print('.')
        output = mtda.console_flush()
        if "Boot Manager" in output:
            mtda.debug(1, "Entered Main Menu")
            mtda.console_clear()
            return True
        sleep(0.25)
    return False


def qemu_bios_main_reset():
    qemu_bios_main_menu()
    mtda.debug(1, "Resetting the system")
    qemu_select_item("\x1b[0m\x1b[34m\x1b[47m\x1b[08;58HReset")

def qemu_enter_secureboot_config():
    mtda.debug(1, "Entering Device Manager")
    mtda.console_send('\x1b[B\r')
    sleep(0.5)
    mtda.debug(1, "Entering Secure Boot Configuration")
    mtda.console_send('\r')
    sleep(0.5)
    return True


def qemu_enter_boot_manager():
    mtda.debug(1, "Entering Boot Manager")
    mtda.console_send('\x1b[B\x1b[B\r')
    sleep(0.5)
    mtda.console_clear()
    return True


def qemu_boot_from_usb():
    qemu_bios_main_menu() and \
            qemu_enter_boot_manager() and \
            qemu_select_item("QEMU USB")


def qemu_toggle_secureboot(state):
    status = 'Enabled' if state is False else 'Disabled'
    state = '[X]' if state is False else '[ ]'

    qemu_bios_main_menu()
    qemu_enter_secureboot_config()

    output = mtda.console_flush()
    if status in output:
        qemu_select_item(state)
        mtda.console_send('\r')
    qemu_bios_main_reset()


def qemu_disable_secureboot():
    qemu_toggle_secureboot(False)
    return 0

def qemu_enable_secureboot():
    qemu_toggle_secureboot(True)
    return 0


def qemu_reset_tpm():
    qemu_disable_secureboot()

    qemu_bios_main_menu()
    qemu_enter_secureboot_config()

    qemu_select_item("\x1b[0m\x1b[37m\x1b[40m\x1b[09;04HReset Secure Boot Keys")
    mtda.console_send('\r')

    qemu_bios_main_reset()
    return 0

def qemu_power_on():
    scripts.check_reset_tpm() or \
        scripts.check_disable_secureboot() or \
        scripts.check_enable_secureboot() or \
        scripts.check_boot_from_usb()


def qemu_select_item(target, tries=10):
    mtda.debug(1, f"wanting to select '{target}'")

    output = ""
    while target not in output and tries > 0:
         mtda.console_send('\x1b[B')
         sleep(1.5)
         output = mtda.console_flush()
         tries = tries - 1
    if tries > 0:
        sleep(0.5)
        mtda.console_send('\r')
        return True
    return False


def qemu_boot_from_usb():
    mtda.debug(1, "wanting to boot from USB")
    qemu_bios_main_menu()
    qemu_enter_boot_manager()
    qemu_select_item("QEMU USB")
