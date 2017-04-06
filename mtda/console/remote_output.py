#!/usr/bin/env python3

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
        socket.connect ("tcp://%s:%s" % (self.host, self.port))
        socket.setsockopt(zmq.SUBSCRIBE, b'')
        while True:
            data = socket.recv()
            sys.stdout.buffer.write(data)
            sys.stdout.flush()

