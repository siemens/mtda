# ---------------------------------------------------------------------------
# QEMU video capture for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
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
        self.qemu = mtda.power_controller

    def configure(self, conf):
        self.mtda.debug(3, "video.qemu.configure()")

        result = True
        if 'sink' in conf:
            self.sink = conf['sink']

        self.mtda.debug(3, "video.qemu.configure(): " "%s" % str(result))
        return result

    def probe(self):
        self.mtda.debug(3, "video.qemu.probe()")

        result = self.qemu.variant == "qemu"
        if result is False:
            self.mtda.debug(1, "video.qemu.probe(): "
                            "qemu power controller required!")

        self.mtda.debug(3, "video.qemu.probe(): %s" % str(result))
        return result

    def start(self):
        return True

    def stop(self):
        return True

    def url(self, host="", opts=None):
        self.mtda.debug(3, "video.qemu.url(host={0}, "
                           "opts={1}".format(host, opts))

        if host is None or host == "":
            host = socket.getfqdn()
            self.mtda.debug(3, "video.qemu.url: using host='%s'" % str(host))
        result = 'gst-pipeline: rfbsrc host={0} ! {1}'.format(host, self.sink)
        if opts is not None:
            if 'sink' in opts:
                if 'name' in opts['sink']:
                    result += ' name="{0}"'.format(opts['sink']['name'])

        self.mtda.debug(3, "video.qemu.url(): %s" % str(result))
        return result


def instantiate(mtda):
    return QemuVideoController(mtda)
