# ---------------------------------------------------------------------------
# Console output for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2021 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import collections
import os
import sys
import threading


class ConsoleOutput:

    def __init__(self, screen):
        self.exiting = False
        self.rx_alive = False
        self.rx_lock = threading.Lock()
        self.rx_paused = False
        self.rx_queue = collections.deque(maxlen=1000)
        self.rx_thread = None
        self.screen = screen

    def on_event(self, event):
        self.screen.on_event(event)

    def _pause(self):
        self.rx_paused = True

    def pause(self):
        with self.rx_lock:
            self._pause()

    def print(self, data):
        self.screen.print(data)

    def reader(self):
        return None

    def _resume(self):
        while len(self.rx_queue) > 0:
            data = self.rx_queue.popleft()
            self.print(data)
        self.rx_paused = False

    def resume(self):
        with self.rx_lock:
            self._resume()

    def start(self):
        self.rx_alive = True
        self.rx_thread = threading.Thread(
            target=self.reader, name='console_rx')
        self.rx_thread.daemon = True
        self.rx_thread.start()

    def stop(self):
        self.exiting = True

    def toggle(self):
        with self.rx_lock:
            if self.rx_paused is True:
                self._resume()
            else:
                self._pause()

    def write(self, data):
        with self.rx_lock:
            if self.rx_paused is False:
                self.print(data)
            else:
                self.rx_queue.append(data)
