#!/usr/bin/env python3

# System imports
from   collections import deque
import os
import sys
import threading

class ConsoleLogger:

    def __init__(self, console):
        self.console = console
        self.rx_alive = False
        self.rx_thread = None
        self.rx_queue = bytearray()
        self.rx_buffer = deque(maxlen=1000)

    def start(self):
        self.rx_alive = True
        self.rx_thread = threading.Thread(target=self.reader, name='console_rx')
        self.rx_thread.daemon = True
        self.rx_thread.start()

    def process_rx(self, data):
        # Add received data to the RX queue
        self.rx_queue.extend(data)
        # Find lines we have in the queue
        while True:
            off = self.rx_queue.find(b'\r', 0)
            if off >= 0:
                # Add this line to the circular buffer
                line = self.rx_queue[0:off]
                self.rx_buffer.append(line)
                # Remove consumed bytes from the queue
                self.rx_queue = self.rx_queue[off+1:]
                # Write this line to stdout
                sys.stdout.buffer.write(line)
                sys.stdout.buffer.flush()
            else:
                break

    def reader(self):
        try:
            con = self.console
            while self.rx_alive == True:
                data = con.read(con.pending() or 1)
                self.process_rx(data)
        except Exception as e:
            self.rx_alive = False
            print("read error on the console (%s)!" % e.strerror, file=sys.stderr)

