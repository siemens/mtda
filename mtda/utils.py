# ---------------------------------------------------------------------------
# Utility classes/functions
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2021 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import os
import psutil
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
