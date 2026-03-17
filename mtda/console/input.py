# ---------------------------------------------------------------------------
# Console input for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2021 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import array
import atexit
import codecs
import fcntl
import os
import select
import termios
import sys
import tty


class ConsoleInput:

    def __init__(self):
        if sys.version_info.major >= 3 and sys.version_info.minor >= 7:
            sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
        else:
            sys.stdin = codecs.getreader('utf-8')(sys.stdin.detach())
        if sys.stdin.isatty():
            self.fd = sys.stdin.fileno()
            self.old = termios.tcgetattr(self.fd)
            atexit.register(self.cleanup)

    def start(self):
        if sys.stdin.isatty():
            new = termios.tcgetattr(self.fd)
            new[3] = new[3] & ~termios.ICANON & ~termios.ECHO & ~termios.ISIG
            new[6][termios.VMIN] = 0
            new[6][termios.VTIME] = 0
            termios.tcsetattr(self.fd, termios.TCSANOW, new)
            tty.setraw(sys.stdin)

    def getkey(self):
        # Block until at least one byte is available, then ask the kernel
        # exactly how many bytes can be read without blocking (FIONREAD) and
        # drain them all in one read.  This naturally batches multi-byte
        # sequences so they are forwarded in a single console_send RPC
        # instead of N separate ones, which would fragment the sequence
        # and confuse TUI programs.
        select.select([self.fd], [], [])
        buf = array.array('i', [0])
        fcntl.ioctl(self.fd, termios.FIONREAD, buf)
        n = max(buf[0], 1)
        data = os.read(self.fd, n)
        # Map DEL (0x7f, sent by the Backspace key on most terminals) to BS
        return data.replace(b'\x7f', b'\x08')

    def cancel(self):
        if sys.stdin.isatty():
            fcntl.ioctl(self.fd, termios.TIOCSTI, b'\0')

    def cleanup(self):
        if sys.stdin.isatty():
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
