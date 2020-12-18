# ---------------------------------------------------------------------------
# Screen output for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (c) Mentor, a Siemens business, 2017-2020
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import codecs
import json
import os
import shutil
import sys
import time
import threading


class ScreenOutput:

    def __init__(self, mtda):
        self.lock = threading.Lock()
        self.mtda = mtda
        self.capture_fd = None
        self.capture_time = None

    def print(self, data):
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
        with self.lock:
            if self.capture_fd is not None:
                delta = time.monotonic_ns() - self.capture_time
                delta = delta / 1000000000.0
                data = json.dumps(data.decode("latin-1"))
                entry = '[%0.6f, "o", %s]\n' % (delta, data)
                self.capture_fd.write(entry)

    def capture_enabled(self):
        return self.capture_fd is not None

    def capture_start(self):
        with self.lock:
            if self.capture_fd is None:
                self.capture_time = time.monotonic_ns()
                fd = open("screen.cast", "w")
                dim = shutil.get_terminal_size((80, 25))
                env = {}
                env["SHELL"] = os.environ["SHELL"]
                env["TERM"] = os.environ["TERM"]
                header = {}
                header["env"] = env
                header["timestamp"] = self.capture_time
                header["version"] = 2
                header["width"] = dim.columns
                header["height"] = dim.lines
                fd.write(json.dumps(header))
                fd.write("\n")
                self.capture_fd = fd

    def capture_stop(self):
        with self.lock:
            if self.capture_fd is not None:
                self.capture_fd.close()
                self.capture_fd = None
