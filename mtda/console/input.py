#!/usr/bin/env python3

# System imports
import atexit
import fcntl
import termios
import sys


class ConsoleInput:

    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        atexit.register(self.cleanup)

    def start(self):
        new = termios.tcgetattr(self.fd)
        new[3] = new[3] & ~termios.ICANON & ~termios.ECHO & ~termios.ISIG
        new[6][termios.VMIN] = 1
        new[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, new)

    def getkey(self):
        c = sys.stdin.read(1)
        if c == chr(0x7f):
            c = chr(8)  # map the BS key (which yields DEL) to backspace
        return c

    def cancel(self):
        fcntl.ioctl(self.fd, termios.TIOCSTI, b'\0')

    def cleanup(self):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
