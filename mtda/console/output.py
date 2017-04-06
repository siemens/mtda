#!/usr/bin/env python3

# System imports
import os
import sys
import threading

class ConsoleOutput:

    def __init__(self):
        self.rx_alive = False
        self.rx_thread = None

    def start(self):
        self.rx_alive = True
        self.rx_thread = threading.Thread(target=self.reader, name='console_rx')
        self.rx_thread.daemon = True
        self.rx_thread.start()

    def reader(self):
        return None

