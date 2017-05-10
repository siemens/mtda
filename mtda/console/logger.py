#!/usr/bin/env python3

# System imports
import codecs
from   collections import deque
import os
import sys
import threading
import time

class ConsoleLogger:

    def __init__(self, console, socket=None):
        self.console = console
        self.rx_alive = False
        self.rx_lines = 0
        self.rx_thread = None
        self.rx_queue = bytearray()
        self.rx_buffer = deque(maxlen=1000)
        self.rx_lock = threading.Lock()
        self.socket = socket
        self.basetime = 0
        self.timestamps = False

    def start(self):
        self.rx_alive = True
        self.rx_thread = threading.Thread(target=self.reader, name='console_rx')
        self.rx_thread.daemon = True
        self.rx_thread.start()

    def head(self):
        self.rx_lock.acquire()
        if self.rx_lines > 0:
            line = self.rx_buffer.popleft().decode("utf-8")
            self.rx_lines -= 1
        else:
            line = None
        self.rx_lock.release()
        return line

    def lines(self):
        self.rx_lock.acquire()
        lines = self.rx_lines
        self.rx_lock.release()
        return lines

    def write(self, data):
        try:
            data = codecs.escape_decode(bytes(data, "utf-8"))[0]
            self.console.write(data)
        except Exception as e:
            print("write error on the console (%s)!" % e.strerror, file=sys.stderr)

    def reset_timer(self):
        self.basetime = 0

    def toggle_timestamps(self):
        self.timestamps = not self.timestamps

    def process_rx(self, data):
        # Initialize basetime on the 1st byte we receive
        if not self.basetime:
            self.basetime = time.time()

        # Add timestamps
        if self.timestamps == True:
            newdata = bytearray()
            linefeeds = 0
            for x in data:
                if x == 0xd:
                    continue
                newdata.append(x)
                if x == 0xa:
                    linetime = time.time()
                    elapsed = linetime - self.basetime
                    timestr = "[%4.6f] " % elapsed
                    newdata.extend(timestr.encode("utf-8"))
                    linefeeds = linefeeds + 1
            data = newdata
        else:
            linefeeds = 1

        # Publish received data
        if self.socket is not None:
            self.socket.send(data)
        else:
            # Write to stdout if received are not pushed to the network
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()

        # Add received data to the RX queue
        self.rx_queue.extend(data)

        # Find lines we have in the queue
        while linefeeds > 0:
            off = self.rx_queue.find(b'\n', 0)
            if off >= 0:
                # Extract line from the RX queue
                off = off + 1
                line = self.rx_queue[:off]

                # Add this line to the circular buffer
                self.rx_lock.acquire()
                self.rx_buffer.append(line)
                self.rx_lines += 1
                self.rx_lock.release()

                # Remove consumed bytes from the queue
                self.rx_queue = self.rx_queue[off+1:]
            else:
                linefeeds = 0

    def reader(self):
        try:
            con = self.console
            while self.rx_alive == True:
                data = con.read(con.pending() or 1)
                self.process_rx(data)
        except Exception as e:
            self.rx_alive = False
            print("read error on the console (%s)!" % e.strerror, file=sys.stderr)

