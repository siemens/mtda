# ---------------------------------------------------------------------------
# Remote console support for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (c) Mentor, a Siemens business, 2017-2020
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# Local imports
from mtda.console.output import ConsoleOutput
import mtda.constants as CONSTS

# System imports
import collections
import zmq


class RemoteConsole(ConsoleOutput):

    def __init__(self, host, port, screen):
        ConsoleOutput.__init__(self, screen)
        self.host = host
        self.port = port
        self.topic = CONSTS.CHANNEL.CONSOLE

    def connect(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://%s:%s" % (self.host, self.port))
        socket.setsockopt(zmq.SUBSCRIBE, self.topic)
        return socket

    def dispatch(self, topic, data):
        self.write(data)

    def reader(self):
        socket = self.connect()
        while self.exiting is False:
            topic, data = socket.recv_multipart()
            self.dispatch(topic, data)


class RemoteMonitor(RemoteConsole):

    def __init__(self, host, port, screen):
        super().__init__(host, port, screen)
        self.topic = CONSTS.CHANNEL.MONITOR

    def connect(self):
        socket = super().connect()
        socket.setsockopt(zmq.SUBSCRIBE, CONSTS.CHANNEL.EVENTS)
        return socket

    def dispatch(self, topic, data):
        if topic != CONSTS.CHANNEL.EVENTS:
            self.write(data)
        else:
            self.on_event(data.decode("utf-8"))
