# ---------------------------------------------------------------------------
# Utility classes/functions
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import os
import psutil
import re
import signal
import threading
import time
import mtda.constants as CONSTS


class Compression:
    def from_extension(path):
        if path.endswith(".bz2"):
            result = CONSTS.IMAGE.BZ2.value
        elif path.endswith(".gz"):
            result = CONSTS.IMAGE.GZ.value
        elif path.endswith(".zst"):
            result = CONSTS.IMAGE.ZST.value
        elif path.endswith(".xz"):
            result = CONSTS.IMAGE.XZ.value
        else:
            result = CONSTS.IMAGE.RAW.value
        return result


class RepeatTimer(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class Size:
    @staticmethod
    def to_bytes(value, default_suffix: str = "") -> int:
        """
        Convert strings like '10K', '5MB', '2GiB', '42'
        """

        if isinstance(value, (int, float)):
            value = str(value)
        value = value.strip()

        m = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]*)", value)
        if not m:
            raise ValueError(f"Invalid size format: {value}")

        number, suffix = m.groups()
        number = float(number)
        if not suffix and default_suffix:
            suffix = default_suffix

        suffix = suffix.upper()
        MULTIPLIERS = {
            "":     1,
            "B":    1,
            "K":    1000,
            "KB":   1000,
            "M":    1000**2,
            "MB":   1000**2,
            "G":    1000**3,
            "GB":   1000**3,
            "KIB":  1024,
            "MIB":  1024**2,
            "GIB":  1024**3,
        }

        if suffix not in MULTIPLIERS:
            raise ValueError(f"Unknown size suffix: '{suffix}'")
        return int(number * MULTIPLIERS[suffix])


class System():
    def kill(name, pid, timeout=3):
        pid = int(pid)
        tries = timeout
        if psutil.pid_exists(pid):
            os.kill(pid, signal.SIGTERM)
        while tries > 0 and psutil.pid_exists(pid):
            time.sleep(1)
            tries = tries - 1
        if psutil.pid_exists(pid):
            os.kill(pid, signal.SIGKILL)
        return psutil.pid_exists(pid)


class SystemdDeviceUnit():
    def create_device_dependency(dropin_path: str, device_path: str):
        """
        Create a systemd drop-in file to wait for a specific device
        to become available.
        """
        # escape device name according to systemd.unit requirements
        device = device_path[1:].replace('-', '\\x2d').replace('/', '-')
        with open(dropin_path, 'w') as f:
            f.write('[Unit]\n')
            f.write(f'Wants={device}.device\n')
            f.write(f'After={device}.device\n')
