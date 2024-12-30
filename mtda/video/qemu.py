# ---------------------------------------------------------------------------
# QEMU video capture for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import socket

# Local imports
from mtda.video.controller import VideoController


class QemuVideoController(VideoController):

    def __init__(self, mtda):
        self.mtda = mtda
        self.sink = "xvimagesink"
        self.qemu = mtda.power

    def configure(self, conf):
        self.mtda.debug(3, "video.qemu.configure()")

        result = True
        if 'sink' in conf:
            self.sink = conf['sink']

        self.mtda.debug(3, f"video.qemu.configure(): {str(result)}")
        return result

    @property
    def format(self):
        return "VNC"

    def probe(self):
        self.mtda.debug(3, "video.qemu.probe()")

        result = self.qemu.variant == "qemu"
        if result is False:
            self.mtda.debug(1, "video.qemu.probe(): "
                            "qemu power controller required!")

        self.mtda.debug(3, f"video.qemu.probe(): {str(result)}")
        return result

    def start(self):
        return True

    def stop(self):
        return True

    def url(self, host="", opts=None):
        self.mtda.debug(3, f"video.qemu.url(host={host}, opts={opts}")

        if host is None or host == "":
            host = socket.getfqdn()
            self.mtda.debug(3, f"video.qemu.url: using host='{str(host)}'")
        result = f'gst-pipeline: rfbsrc host={host} ! {self.sink}'
        if opts is not None:
            if 'sink' in opts:
                if 'name' in opts['sink']:
                    result += f" name=\"{opts['sink']['name']}\""

        self.mtda.debug(3, f"video.qemu.url(): {str(result)}")
        return result


def instantiate(mtda):
    return QemuVideoController(mtda)
