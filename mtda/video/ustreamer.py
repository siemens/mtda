# ---------------------------------------------------------------------------
# ustreamer driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2023 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import os
import socket
import threading
import signal
import subprocess

# Local imports
from mtda.video.controller import VideoController


class UStreamerVideoController(VideoController):

    def __init__(self, mtda):
        self.dev = "/dev/video0"
        self.executable = "ustreamer"
        self.lock = threading.Lock()
        self.mtda = mtda
        self.worker = None
        self.ustreamer = None
        self.port = 8080
        self.desired_fps = 30
        self.resolution = "1280x780"
        self.www = None

    def configure(self, conf):
        self.mtda.debug(3, "video.ustreamer.configure()")

        if 'device' in conf:
            self.dev = conf['device']
            self.mtda.debug(4, 'video.ustreamer.configure(): '
                               'will use %s' % str(self.dev))
        if 'executable' in conf:
            self.executable = conf['executable']
        if 'port' in conf:
            self.port = conf['port']
        if 'resolution' in conf:
            self.resolution = conf['resolution']
        if 'www' in conf:
            self.www = conf['www']

    def configure_systemd(self, dir):
        device = os.path.basename(self.dev)
        dropin = os.path.join(dir, 'auto-dep-video.conf')
        with open(dropin, 'w') as f:
            f.write('[Unit]\n')
            f.write('Wants=dev-{}.device\n'.format(device))
            f.write('After=dev-{}.device\n'.format(device))

    @property
    def format(self):
        return "MJPG"

    def probe(self):
        self.mtda.debug(3, 'video.ustreamer.probe()')

        if self.executable is None:
            raise ValueError('ustreamer executable not specified!')

        result = True
        try:
            subprocess.check_call([self.executable, '--version'])
        except subprocess.SubprocessError as e:
            self.mtda.debug(1, 'error calling %s: %s', self.executable, str(e))
            result = False

        self.mtda.debug(3, 'video.ustreamer.probe(): %s' % str(result))
        return result

    def start(self):
        self.mtda.debug(3, 'video.ustreamer.start()')

        options = [
            '-d', self.dev, '-r', self.resolution,
            '-s', '0.0.0.0',
            '-p', str(self.port),
            '--drop-same-frames', '30',
            '-c', 'HW',    # do not transcode frames (if supported)
            '-f', str(self.desired_fps),
            '--slowdown',  # capture with 1 fps when no client
            ]
        if self.www:
            options += ['--static', self.www]

        with self.lock:
            self.ustreamer = subprocess.Popen([self.executable] + options)

        return True

    def stop(self):
        self.mtda.debug(3, 'video.ustreamer.stop()')

        with self.lock:
            if self.ustreamer.poll() is None:
                self.ustreamer.send_signal(signal.SIGINT)
            try:
                self.ustreamer.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.mtda.debug(2, 'video.ustreamer.stop: '
                                   'process did not finish, killing')
                self.ustreamer.kill()

        return True

    def url(self, host="", opts=None):
        self.mtda.debug(3, "video.ustreamer.url(host='%s')" % str(host))

        if host is None or host == "":
            host = socket.getfqdn()
            self.mtda.debug(3, "video.ustreamer.url: "
                               "using host='%s'" % str(host))
        result = "http://{0}:{1}/?action=stream".format(host, self.port)

        self.mtda.debug(3, 'video.ustreamer.url(): %s' % str(result))
        return result


def instantiate(mtda):
    return UStreamerVideoController(mtda)
