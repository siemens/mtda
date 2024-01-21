# ---------------------------------------------------------------------------
# mjpg_streamer driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2024 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import atexit
import os
import psutil
import signal
import socket
import threading
import time

# Local imports
from mtda.video.controller import VideoController
from mtda.utils import SystemdDeviceUnit


class MJPGStreamerVideoController(VideoController):

    def __init__(self, mtda):
        self.dev = "/dev/video0"
        self.executable = "mjpg_streamer"
        self.input = "-i 'input_uvc.so -d {0} -r {1}'"
        self.lock = threading.Lock()
        self.mtda = mtda
        self.output = "-o 'output_http.so -p {0} -w {1}'"
        self.pid = None
        self.port = 8080
        self.resolution = "1280x780"
        self.www = "/usr/share/mjpg-streamer/www"

    def configure(self, conf):
        self.mtda.debug(3, "video.mjpg_streamer.configure()")
        self.mtda.debug(2, "video.mjpg_streamer is deprecated. "
                           "Use video.ustreamer instead")

        if 'device' in conf:
            self.dev = conf['device']
            self.mtda.debug(4, "video.mjpg_streamer.configure(): "
                               "will use %s" % str(self.dev))
        if 'executable' in conf:
            self.executable = conf['executable']
        if 'port' in conf:
            self.port = conf['port']
        if 'resolution' in conf:
            self.resolution = conf['resolution']
        if 'www' in conf:
            self.www = conf['www']

    def configure_systemd(self, dir):
        dropin = os.path.join(dir, 'auto-dep-video.conf')
        SystemdDeviceUnit.create_device_dependency(dropin, self.dev)

    @property
    def format(self):
        return "MJPG"

    def probe(self):
        self.mtda.debug(3, "video.mjpg_streamer.probe()")

        if self.executable is None:
            raise ValueError("mjpg_streamer executable not specified!")

        result = True
        if os.system(f"{self.executable} --version") != 0:
            raise ValueError(f"could not execute {self.executable}!")
        if os.path.exists(self.dev) is False:
            self.mtda.debug(1, "video.mjpg_streamer.probe(): "
                               "video device (%s) not found!"
                               % self.dev)
            result = False

        self.mtda.debug(3, f"video.mjpg_streamer.probe(): {str(result)}")
        return result

    def getpid(self):
        name = os.path.basename(self.executable)
        pid = None

        for proc in psutil.process_iter():
            if name in proc.name():
                pid = proc.pid
                break

        return pid

    def start(self):
        self.mtda.debug(3, "video.mjpg_streamer.start()")

        if self.pid is not None:
            return True

        atexit.register(self.stop)

        options = self.input.format(self.dev, self.resolution)
        options += " "
        options += self.output.format(self.port, self.www)
        options += " -b"

        result = os.system(f"{self.executable} {options}")
        if result == 0:
            self.pid = self.getpid()
            self.mtda.debug(2, "video.mjpg_streamer.start(): "
                               "mjpg_streamer process started "
                               "[{0}]".format(self.pid))
            return True
        else:
            self.mtda.debug(1, "video.mjpg_streamer.start(): "
                               "mjpg_streamer process failed "
                               "({0})".format(result))
        return False

    def kill(self, name, pid, timeout=3):
        tries = timeout
        if psutil.pid_exists(pid):
            self.mtda.debug(2, f"terminating {name} [{pid}] using SIGTERM")
            os.kill(pid, signal.SIGTERM)
        while tries > 0 and psutil.pid_exists(pid):
            time.sleep(1)
            tries = tries - 1
        if psutil.pid_exists(pid):
            self.mtda.debug(2, f"terminating {name} [{pid}] using SIGKILL")
            os.kill(pid, signal.SIGKILL)
        return psutil.pid_exists(pid)

    def stop(self):
        self.mtda.debug(3, "video.mjpg_streamer.stop()")

        self.lock.acquire()
        result = True

        if self.pid is not None:
            name = os.path.basename(self.executable)
            result = self.kill(name, self.pid)
            if result:
                self.pid = None

        self.lock.release()
        self.mtda.debug(3, f"video.mjpg_streamer.stop(): {str(result)}")
        return result

    def url(self, host="", opts=None):
        self.mtda.debug(3, f"video.mjpg_streamer.url(host='{str(host)}')")

        if host is None or host == "":
            host = socket.getfqdn()
            self.mtda.debug(3, "video.mjpg_streamer."
                               f"url: using host='{str(host)}'")
        result = f"http://{host}:{self.port}/?action=stream"

        self.mtda.debug(3, f"video.mjpg_streamer.url(): {str(result)}")
        return result


def instantiate(mtda):
    return MJPGStreamerVideoController(mtda)
