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

import threading


class RepeatTimer(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


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
