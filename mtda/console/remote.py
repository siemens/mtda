# ---------------------------------------------------------------------------
# Remote console support for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# Local imports
from mtda.console.output import ConsoleOutput
import mtda.constants as CONSTS

# System imports
import zmq


class RemoteConsole(ConsoleOutput):

    def __init__(self, host, port, screen):
        ConsoleOutput.__init__(self, screen)
        self.context = None
        self.host = host
        self.port = port
        self.socket = None
        self.topic = CONSTS.CHANNEL.CONSOLE

    def connect(self):
        self.context = self._context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"tcp://{self.host}:{self.port}")
        self._subscribe()

    def _context(self):
        return zmq.Context()

    def _subscribe(self):
        self.socket.setsockopt(zmq.SUBSCRIBE, self.topic)

    def dispatch(self, topic, data):
        if topic != CONSTS.CHANNEL.EVENTS:
            self.write(data)
        else:
            self.on_event(data.decode("utf-8"))

    def reader(self):
        self.connect()
        try:
            while self.exiting is False:
                topic, data = self.socket.recv_multipart()
                self.dispatch(topic, data)
        except zmq.error.ContextTerminated:
            self.socket = None

    def stop(self):
        super().stop()
        if self.context is not None:
            self.context.term()
            self.context = None


class RemoteMonitor(RemoteConsole):

    def __init__(self, host, port, screen):
        super().__init__(host, port, screen)
        self.topic = CONSTS.CHANNEL.MONITOR

    def _subscribe(self):
        super()._subscribe()
        self.socket.setsockopt(zmq.SUBSCRIBE, CONSTS.CHANNEL.EVENTS)
