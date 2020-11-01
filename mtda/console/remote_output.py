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
import sys
import zmq


class RemoteConsoleOutput(ConsoleOutput):

    def __init__(self, host, port):
        ConsoleOutput.__init__(self)
        self.host = host
        self.port = port

    def reader(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://%s:%s" % (self.host, self.port))
        socket.setsockopt(zmq.SUBSCRIBE, b'')
        while True:
            data = socket.recv()
            sys.stdout.buffer.write(data)
            sys.stdout.flush()
