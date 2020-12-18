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

# System imports
import collections
import zmq


class RemoteConsoleOutput(ConsoleOutput):

    def __init__(self, host, port, screen, topic=b'CON'):
        ConsoleOutput.__init__(self, screen)
        self.host = host
        self.port = port
        self.topic = topic

    def reader(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://%s:%s" % (self.host, self.port))
        socket.setsockopt(zmq.SUBSCRIBE, self.topic)
        while True:
            topic, data = socket.recv_multipart()
            self.write(data)
