#!/usr/bin/env python3

# System imports
import os
import sys
import threading

class ConsoleLogger:

    def __init__(self, console):
        self.console = console
        self.rx_alive = False
        self.rx_thread = None

    def start(self):
        self.rx_alive = True
        self.rx_thread = threading.Thread(target=self.reader, name='console_rx')
        self.rx_thread.daemon = True
        self.rx_thread.start()

    def reader(self):
        try:
            con = self.console
            while self.rx_alive == True:
                data = con.read(con.pending() or 1)
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
        except Exception as e:
            self.rx_alive = False
            print("read error on the console (%s)!" % e.strerror, file=sys.stderr)

