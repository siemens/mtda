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
        self._prompt = "=> "
        self.rx_alive = False
        self.rx_thread = None
        self.rx_queue = bytearray()
        self.rx_buffer = deque(maxlen=1000)
        self.rx_lock = threading.Lock()
        self.rx_cond = threading.Condition(self.rx_lock)
        self.socket = socket
        self.basetime = 0
        self.timestamps = False

    def start(self):
        self.rx_alive = True
        self.rx_thread = threading.Thread(target=self.reader, name='console_rx')
        self.rx_thread.daemon = True
        self.rx_thread.start()

    def _clear(self):
        self.rx_buffer.clear()
        self.rx_queue = bytearray()

    def clear(self):
        self.rx_lock.acquire()
        self._clear()
        self.rx_lock.release()

    def _flush(self):
        data = ""
        lines = len(self.rx_buffer)
        while lines > 0:
            line = self.rx_buffer.popleft().decode("utf-8")
            data = data + line
            lines = lines - 1
        line = self.rx_queue.decode("utf-8")
        data = data + line
        self.rx_queue = bytearray()
        return data

    def flush(self):
        self.rx_lock.acquire()
        data = self._flush()
        self.rx_lock.release()
        return data

    def _head(self):
        if len(self.rx_buffer) > 0:
            line = self.rx_buffer.popleft().decode("utf-8")
        else:
            line = None
        return line

    def head(self):
        self.rx_lock.acquire()
        line = self._head()
        self.rx_lock.release()
        return line

    def lines(self):
        self.rx_lock.acquire()
        lines = len(self.rx_buffer)
        self.rx_lock.release()
        return lines

    def _matchprompt(self):
        prompt = self._tail(False)
        if prompt is None:
            return False
        if prompt.startswith("\r"):
            prompt = prompt[1:]
        return prompt.endswith(self._prompt)

    def prompt(self, newPrompt=None):
        self.rx_lock.acquire()
        if newPrompt is not None:
            self._prompt = newPrompt
        p = self._prompt
        self.rx_lock.release()
        return p

    def run(self, cmd):
        self.rx_lock.acquire()
        self._clear()

        # Send a break to get a prompt
        self.write("\3")

        # Wait for a prompt
        self.rx_cond.wait_for(self._matchprompt)

        # Send requested command
        self._clear()
        self.write("%s\n" % (cmd))

        # Wait for the command to complete
        self.rx_cond.wait_for(self._matchprompt)

        # Strip first line (command we sent) and flush received bytes
        self._head()
        data = self._flush()

        # Release and return command output
        self.rx_lock.release()
        return data

    def _tail(self, discard=True):
        if len(self.rx_queue) > 0:
            line = self.rx_queue
        elif len(self.rx_buffer) > 0:
            line = self.rx_buffer[-1]
        else:
            return None
        if discard == True:
            self._clear()
        return line.decode("utf-8")

    def tail(self):
        self.rx_lock.acquire()
        line = self._tail()
        self.rx_lock.release()
        return line

    def write(self, data, raw=False):
        try:
            if raw == False:
                data = codecs.escape_decode(bytes(data, "utf-8"))[0]
            else:
                data = bytes(data, "utf-8")
            self.console.write(data)
        except Exception as e:
            print("write error on the console (%s)!" % e.strerror, file=sys.stderr)

    def reset_timer(self):
        self.basetime = 0

    def toggle_timestamps(self):
        self.timestamps = not self.timestamps

    # Print bytes to the console (local or remote)
    def _print(self, data):
        if self.socket is not None:
            self.socket.send(data)
        else:
            # Write to stdout if received are not pushed to the network
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()

    # Print a string to the console (local or remote)
    def print(self, data):
        data = codecs.escape_decode(bytes(data, "utf-8"))[0]
        self._print(data)

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
        self._print(data)

        # Prevent concurrent access to the RX buffers
        self.rx_lock.acquire()

        # Add received data
        self.rx_queue.extend(data)

        # Find lines we have in the queue
        while linefeeds > 0:
            sz = len(self.rx_queue)
            off = self.rx_queue.find(b'\n', 0)
            if off >= 0:
                # Will include the line feed character in the buffered line
                off  = off + 1
                rem  = sz - off

                # Extract line from the RX queue
                line = self.rx_queue[:off]

                # Strip trailing \r
                if len(line) > 1 and line[-2] == 0xd and line[-1] == 0xa:
                    del line[-1:]
                    line[-1] = 0xa

                # Add this line to the circular buffer
                self.rx_buffer.append(line)

                # Remove consumed bytes from the queue
                if rem > 0:
                    self.rx_queue = self.rx_queue[-rem:]
                else:
                    self.rx_queue = bytearray()
            else:
                linefeeds = 0

        # Notify threads waiting on data
        self.rx_cond.notify()

        # Release access to the RX buffers
        self.rx_lock.release()

    def reader(self):
        try:
            con = self.console
            while self.rx_alive == True:
                data = con.read(con.pending() or 1)
                self.process_rx(data)
        except Exception as e:
            self.rx_alive = False
            print("read error on the console (%s)!" % e.strerror, file=sys.stderr)

