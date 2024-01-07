# ---------------------------------------------------------------------------
# Support for USB Composite
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2024 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import atexit
import os
import threading


class Composite:

    mtda = None
    lock = threading.Lock()
    vendor_id = "0x1d6b"  # Linux Foundation
    product_id = "0x0104"  # Multifunction Composite Gadget
    serialnumber = "mtda-2020"
    manufacturer = "Siemens Digital Industries Software"
    product = "USB functions for Multi-Tenant Device Access"
    lang = "0x409"  # english
    _storage = None
    _installed = False

    path = "/sys/kernel/config/usb_gadget/" + product.lower().replace(" ", "_")

    def debug(level, msg):
        if Composite.mtda is not None:
            Composite.mtda.debug(level, msg)

    def configure(what, conf):
        Composite.debug(3, "composite.configure('{}')".format(what))

        with Composite.lock:
            result = Composite._configure(what, conf)

        Composite.debug(3, "composite.configure(): {}".format(result))
        return result

    def _configure(what, conf):
        result = True
        if what == 'storage':
            # keep this logic in sync with usbf handler (prefer file)
            if 'file' in conf:
                Composite._storage = conf['file']
            elif 'device' in conf:
                Composite._storage = conf['device']
        if what in Composite.functions:
            Composite.functions[what]['configured'] = True
            Composite.functions[what]['enabled'] = True
            Composite.debug(2, "composite.configure(): "
                               "{} configured & enabled".format(what))
        else:
            Composite.debug(1, "composite.configure(): "
                               "not supported")
            result = False

        return result

    def _enable():
        usbdrv = os.listdir("/sys/class/udc")[0]
        udc = os.path.join(Composite.path, "UDC")
        result = write(udc, usbdrv)
        return result > 0

    def _disable():
        udc = os.path.join(Composite.path, "UDC")
        if os.path.exists(udc):
            write(udc, "")
        return True

    def install():
        Composite.debug(3, "composite.install()")

        with Composite.lock:
            result = Composite._install()

        Composite.debug(3, "composite.install(): {}".format(result))
        return result

    def _install():
        if Composite._installed is True:
            return True

        Composite._remove()

        enabled = False
        for function in Composite.functions.values():
            if function['enabled'] is True:
                enabled = True
                break

        if enabled is False:
            # Nothing to install
            Composite.debug(2, "composite.install(): "
                               "no functions were enabled")
            return True

        atexit.register(Composite.remove)
        path = Composite.path
        create_dirs(path)

        write(path + "/idVendor",  Composite.vendor_id)
        write(path + "/idProduct", Composite.product_id)
        write(path + "/bcdDevice", "0x0100")
        write(path + "/bcdUSB", "0x0200")

        strings = path + "/strings/" + Composite.lang + "/"
        write(strings + "serialnumber", Composite.serialnumber)
        write(strings + "manufacturer", Composite.manufacturer)
        write(strings + "product", Composite.product)

        strings = path + "/configs/c.1/strings/" + Composite.lang + "/"
        write(strings + "configuration", "Config 1: ECM network")
        write(path + "/configs/c.1/MaxPower", "250")

        Composite._create_functions()

        if Composite.functions['storage']['enabled'] is True:
            lun = path + "/functions/mass_storage.usb0/lun.0/"
            file = Composite._storage
            write(lun + "cdrom", "0")
            write(lun + "ro", "0")
            write(lun + "nofua", "0")
            write(lun + "file", file)
            Composite.debug(2, "composite.install(): "
                               "storage device/file: {}".format(file))
        Composite._installed = Composite._enable()
        return Composite._installed

    def remove():
        Composite.debug(3, "composite.remove()")

        with Composite.lock:
            result = Composite._remove()

        Composite.debug(3, "composite.remove(): {}".format(result))
        return result

    def _remove():
        lang = Composite.lang
        path = Composite.path

        if os.path.exists(path) is False:
            return

        Composite._disable()

        functions = os.listdir(os.path.join(path, "functions"))
        for function in functions:
            os.unlink(os.path.join(path, "configs", "c.1", function))
        os.rmdir(os.path.join(path, "configs", "c.1", "strings", lang))
        os.rmdir(os.path.join(path, "configs", "c.1"))
        for function in functions:
            os.rmdir(os.path.join(path, "functions", function))
        os.rmdir(os.path.join(path, "strings", lang))
        os.rmdir(path)

        Composite._installed = False

    def _create_functions():
        for function in Composite.functions.values():
            name = function['name']
            if function['configured'] is False:
                continue
            if function['enabled'] is False:
                continue
            Composite.debug(2, "composite._create_functions: "
                               "registering {}".format(name))
            path = Composite.path + "/functions/" + name
            if not os.path.exists(path):
                os.makedirs(path)
            if 'protocol' in function:
                write(path + "/protocol", function['protocol'])
            if 'subclass' in function:
                write(path + "/subclass", function['subclass'])
            if 'report_length' in function:
                write(path + "/report_length", function['report_length'])
            if 'report_desc' in function:
                write(path + "/report_desc", function['report_desc'], "wb")
            config = Composite.path + "/configs/c.1/" + name
            if not os.path.exists(config):
                os.symlink(path, config, True)

    def storage_toggle(enabled):
        with Composite.lock:
            if Composite.functions['storage']['configured'] is True:
                Composite.functions['storage']['enabled'] = enabled

    hid_function = {
        "name": "hid.usb0",
        "configured": False,
        "enabled": False,
        "protocol": "1",
        "subclass": "1",
        "report_length": "8",
        "report_desc": [
            0x05, 0x01,  # USAGE_PAGE (Generic Desktop)
            0x09, 0x06,  # USAGE (Keyboard)
            0xa1, 0x01,  # COLLECTION (Application)
            0x05, 0x07,  # USAGE_PAGE (Keyboard)
            0x19, 0xe0,  # USAGE_MINIMUM (Keyboard LeftControl)
            0x29, 0xe7,  # USAGE_MAXIMUM (Keyboard Right GUI)
            0x15, 0x00,  # LOGICAL_MINIMUM (0)
            0x25, 0x01,  # LOGICAL_MAXIMUM (1)
            0x75, 0x01,  # REPORT_SIZE (1)
            0x95, 0x08,  # REPORT_COUNT (8)
            0x81, 0x02,  # INPUT (Data,Var,Abs)
            0x95, 0x01,  # REPORT_COUNT (1)
            0x75, 0x08,  # REPORT_SIZE (8)
            0x81, 0x01,  # INPUT (Cnst,Var,Abs) // 0x03
            0x95, 0x05,
            0x75, 0x01,
            0x05, 0x08,
            0x19, 0x01,
            0x29, 0x05,
            0x91, 0x02,
            0x95, 0x01,
            0x75, 0x03,
            0x91, 0x01,  # 0x03
            0x95, 0x06,  # REPORT_COUNT (6)
            0x75, 0x08,  # REPORT_SIZE (8)
            0x15, 0x00,  # LOGICAL_MINIMUM (0)
            0x25, 0x65,  # LOGICAL_MAXIMUM (101)
            0x05, 0x07,  # USAGE_PAGE (Keyboard)
            0x19, 0x00,  # USAGE_MINIMUM (Reserved (no event indicated))
            0x29, 0x65,  # USAGE_MAXIMUM (Keyboard Application)
            0x81, 0x00,  # INPUT (Data,Ary,Abs)
            0xc0
        ]
    }

    console_function = {
        "name": "acm.GS0",
        "configured": False,
        "enabled": False
    }

    monitor_function = {
        "name": "acm.GS1",
        "configured": False,
        "enabled": False
    }

    ms_function = {
        "name": "mass_storage.usb0",
        "configured": False,
        "enabled": False
    }

    functions = {
        "console": console_function,
        "monitor": monitor_function,
        "keyboard": hid_function,
        "storage": ms_function
    }


def write(filename, content, mode="w"):
    with open(filename, mode) as fp:
        if type(content) is str:
            return fp.write(content)
        if type(content) is list:
            return fp.write(bytearray(content))


def create_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

    if not os.path.exists(path + "/strings/" + Composite.lang):
        os.makedirs(path + "/strings/" + Composite.lang)

    if not os.path.exists(path + "/configs/c.1/strings/" + Composite.lang):
        os.makedirs(path + "/configs/c.1/strings/" + Composite.lang)
