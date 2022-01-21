# ---------------------------------------------------------------------------
# MTDA main
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import configparser
import importlib
import os
import queue
import socket
import sys
import threading
import time
import zmq

# Local imports
from mtda.console.input import ConsoleInput
from mtda.console.logger import ConsoleLogger
from mtda.console.remote import RemoteConsole, RemoteMonitor
from mtda.storage.writer import AsyncImageWriter
import mtda.constants as CONSTS
import mtda.discovery
import mtda.keyboard.controller
import mtda.power.controller
import mtda.video.controller
import mtda.utils
from mtda import __version__

_NOPRINT_TRANS_TABLE = {
    i: '.' for i in range(0, sys.maxunicode + 1) if not chr(i).isprintable()
}

DEFAULT_PREFIX_KEY = 'ctrl-a'
DEFAULT_PASTEBIN_EP = "http://pastebin.com/api/api_post.php"


def _make_printable(s):
    return s.translate(_NOPRINT_TRANS_TABLE)


class MultiTenantDeviceAccess:

    def __init__(self):
        self.config_files = ['mtda.ini']
        self.console = None
        self.socket = None
        self.console_logger = None
        self.monitor = None
        self.monitor_logger = None
        self.console_input = None
        self.console_output = None
        self.monitor_output = None
        self.debug_level = 0
        self.env = {}
        self.fuse = False
        self.keyboard = None
        self.video = None
        self.mtda = self
        self.name = socket.gethostname()
        self.assistant = None
        self.power_controller = None
        self.power_on_script = None
        self.power_off_script = None
        self.power_monitors = []
        self.storage_controller = None
        self._pastebin_api_key = None
        self._pastebin_endpoint = None
        self._storage_mounted = False
        self._storage_opened = False
        self._writer = None
        self._writer_data = None
        self.blksz = CONSTS.WRITER.READ_SIZE
        self.usb_switches = []
        self.ctrlport = 5556
        self.conport = 5557
        self.prefix_key = self._prefix_key_code(DEFAULT_PREFIX_KEY)
        self.is_remote = False
        self.is_server = False
        self.remote = None
        self._lock_owner = None
        self._lock_expiry = None
        self._power_expiry = None
        self._session_lock = threading.Lock()
        self._session_timer = None
        self._sessions = {}
        self._time_from_pwr = None
        self._time_from_str = None
        self._time_until_str = None
        self._uptime = 0
        self.version = __version__

        # Config file in $HOME/.mtda/config
        home = os.getenv('HOME', '')
        if home != '':
            self.config_files.append(os.path.join(home, '.mtda', 'config'))

        # Config file in /etc/mtda/config
        if os.path.exists('/etc'):
            self.config_files.append(os.path.join('/etc', 'mtda', 'config'))

    def agent_version(self):
        return self.version

    def command(self, args, session=None):
        self.mtda.debug(3, "main.command()")

        self._session_check(session)
        result = False
        if self.power_locked(session) is False:
            result = self.power_controller.command(args)

        self.mtda.debug(3, "main.command(): %s" % str(result))
        return result

    def console_prefix_key(self):
        self.mtda.debug(3, "main.console_prefix_key()")
        return self.prefix_key

    def _prefix_key_code(self, prefix_key):
        prefix_key = prefix_key.lower()
        key_dict = {'ctrl-a': '\x01', 'ctrl-b': '\x02', 'ctrl-c': '\x03',
                    'ctrl-d': '\x04', 'ctrl-e': '\x05', 'ctrl-f': '\x06',
                    'ctrl-g': '\x07', 'ctrl-h': '\x08', 'ctrl-i': '\x09',
                    'ctrl-j': '\x0A', 'ctrl-k': '\x0B', 'ctrl-l': '\x0C',
                    'ctrl-n': '\x0E', 'ctrl-o': '\x0F', 'ctrl-p': '\x10',
                    'ctrl-q': '\x11', 'ctrl-r': '\x12', 'ctrl-s': '\x13',
                    'ctrl-t': '\x14', 'ctrl-u': '\x15', 'ctrl-v': '\x16',
                    'ctrl-w': '\x17', 'ctrl-x': '\x18', 'ctrl-y': '\x19',
                    'ctrl-z': '\x1A'}

        if prefix_key in key_dict:
            key_ascii = key_dict[prefix_key]
            return key_ascii
        else:
            raise ValueError("the prefix key specified '{0}' is not "
                             "supported".format(prefix_key))

    def console_getkey(self):
        self.mtda.debug(3, "main.console_getkey()")
        result = None
        try:
            result = self.console_input.getkey()
        except AttributeError:
            print("Initialize the console using console_init first")
        self.mtda.debug(3, "main.console_getkey(): %s" % str(result))
        return result

    def console_init(self):
        self.console_input = ConsoleInput()
        self.console_input.start()

    def console_clear(self, session=None):
        self.mtda.debug(3, "main.console_clear()")

        self._session_check(session)
        if self.console_locked(session):
            self.mtda.debug(2, "console_clear(): console is locked")
            return None
        if self.console_logger is not None:
            result = self.console_logger.clear()
        else:
            result = None

        self.mtda.debug(3, "main.console_clear(): %s" % str(result))
        return result

    def console_dump(self, session=None):
        self.mtda.debug(3, "main.console_dump()")

        self._session_check(session)
        if self.console_locked(session):
            self.mtda.debug(2, "console_dump(): console is locked")
            return None

        result = None
        if self.console_logger is not None:
            result = self.console_logger.dump()

        self.mtda.debug(3, "main.console_dump(): %s" % str(result))
        return result

    def console_flush(self, session=None):
        self.mtda.debug(3, "main.console_flush()")

        self._session_check(session)
        if self.console_locked(session):
            self.mtda.debug(2, "console_flush(): console is locked")
            return None

        result = None
        if self.console_logger is not None:
            result = self.console_logger.flush()

        self.mtda.debug(3, "main.console_flush(): %s" % str(result))
        return result

    def console_head(self, session=None):
        self.mtda.debug(3, "main.console_head()")

        self._session_check(session)
        result = None
        if self.console_logger is not None:
            result = self.console_logger.head()

        self.mtda.debug(3, "main.console_head(): %s" % str(result))
        return result

    def console_lines(self, session=None):
        self.mtda.debug(3, "main.console_lines()")

        self._session_check(session)
        result = None
        if self.console_logger is not None:
            result = self.console_logger.lines()

        self.mtda.debug(3, "main.console_lines(): %s" % str(result))
        return result

    def console_locked(self, session=None):
        self.mtda.debug(3, "main.console_locked()")

        self._session_check(session)
        result = self._check_locked(session)

        self.mtda.debug(3, "main.console_locked(): %s" % str(result))
        return result

    def console_print(self, data, session=None):
        self.mtda.debug(3, "main.console_print()")

        self._session_check(session)
        result = None
        if self.console_logger is not None:
            result = self.console_logger.print(data)

        self.mtda.debug(3, "main.console_print(): %s" % str(result))
        return result

    def console_prompt(self, newPrompt=None, session=None):
        self.mtda.debug(3, "main.console_prompt()")

        self._session_check(session)
        result = None
        if self.console_locked(session) is False and \
           self.console_logger is not None:
            result = self.console_logger.prompt(newPrompt)

        self.mtda.debug(3, "main.console_prompt(): %s" % str(result))
        return result

    def console_remote(self, host, screen):
        self.mtda.debug(3, "main.console_remote()")

        result = None
        if self.is_remote is True:
            # Stop previous remote console
            if self.console_output is not None:
                self.console_output.stop()
            if host is not None:
                # Create and start our remote console
                self.console_output = RemoteConsole(host, self.conport, screen)
                self.console_output.start()
            else:
                self.console_output = None

        self.mtda.debug(3, "main.console_remote(): %s" % str(result))
        return result

    def console_run(self, cmd, session=None):
        self.mtda.debug(3, "main.console_run()")

        self._session_check(session)
        result = None
        if self.console_locked(session) is False and \
           self.console_logger is not None:
            result = self.console_logger.run(cmd)

        self.mtda.debug(3, "main.console_run(): %s" % str(result))
        return result

    def console_send(self, data, raw=False, session=None):
        self.mtda.debug(3, "main.console_send()")

        self._session_check(session)
        result = None
        if self.console_locked(session) is False and \
           self.console_logger is not None:
            result = self.console_logger.write(data, raw)

        self.mtda.debug(3, "main.console_send(): %s" % str(result))
        return result

    def console_tail(self, session=None):
        self.mtda.debug(3, "main.console_tail()")

        self._session_check(session)
        if self.console_locked(session) is False and \
           self.console_logger is not None:
            result = self.console_logger.tail()

        self.mtda.debug(3, "main.console_tail(): %s" % str(result))
        return result

    def console_toggle(self, session=None):
        self.mtda.debug(3, "main.console_toggle()")

        result = None
        self._session_check(session)
        if self.console_output is not None:
            self.console_output.toggle()
        if self.monitor_output is not None:
            self.monitor_output.toggle()

        self.mtda.debug(3, "main.console_toggle(): %s" % str(result))
        return result

    def console_wait(self, what, timeout=None, session=None):
        self.mtda.debug(3, "main.console_wait()")

        self._session_check(session)
        result = None
        if session is not None and timeout is None:
            self.mtda.debug(1, "main.console_wait(): no timeout specified!")
            timeout = CONSTS.RPC.TIMEOUT
        if self.console_locked(session) is False and \
           self.console_logger is not None:
            result = self.console_logger.wait(what, timeout)

        self.mtda.debug(3, "main.console_wait(): %s" % str(result))
        return result

    def debug(self, level, msg):
        if self.debug_level >= level:
            if self.debug_level == 0:
                prefix = "# "
            else:
                prefix = "# debug%d: " % level
            msg = str(msg).replace("\n", "\n%s ... " % prefix)
            lines = msg.splitlines()
            sys.stderr.buffer.write(prefix.encode("utf-8"))
            for line in lines:
                sys.stderr.buffer.write(_make_printable(line).encode("utf-8"))
                sys.stderr.buffer.write(b"\n")
                sys.stderr.buffer.flush()

    def env_get(self, name, session=None):
        self.mtda.debug(3, "env_get()")

        self._session_check(session)
        result = None
        if name in self.env:
            result = self.env[name]

        self.mtda.debug(3, "env_get(): %s" % str(result))
        return result

    def env_set(self, name, value, session=None):
        self.mtda.debug(3, "env_set()")

        self._session_check(session)
        result = None

        if name in self.env:
            old_value = self.env[name]
            result = old_value
        else:
            old_value = value

        self.env[name] = value
        self.env["_%s" % name] = old_value

        self.mtda.debug(3, "env_set(): %s" % str(result))
        return result

    def keyboard_write(self, input_str, session=None):
        self.mtda.debug(3, "main.keyboard_write()")

        self._session_check(session)
        result = None
        if self.keyboard is not None:
            result = self.keyboard.write(input_str)

        self.mtda.debug(3, "main.keyboard_write(): %s" % str(result))
        return result

    def monitor_remote(self, host, screen):
        self.mtda.debug(3, "main.monitor_remote()")

        result = None
        if self.is_remote is True:
            # Stop previous remote console
            if self.monitor_output is not None:
                self.monitor_output.stop()
            if host is not None:
                # Create and start our remote console in paused
                # (i.e. buffering) state
                self.monitor_output = RemoteMonitor(host, self.conport, screen)
                self.monitor_output.pause()
                self.monitor_output.start()
            else:
                self.monitor_output = None

        self.mtda.debug(3, "main.monitor_remote(): %s" % str(result))
        return result

    def monitor_send(self, data, raw=False, session=None):
        self.mtda.debug(3, "main.monitor_send()")

        self._session_check(session)
        result = None
        if self.console_locked(session) is False and \
           self.monitor_logger is not None:
            result = self.monitor_logger.write(data, raw)

        self.mtda.debug(3, "main.monitor_send(): %s" % str(result))
        return result

    def monitor_wait(self, what, timeout=None, session=None):
        self.mtda.debug(3, "main.monitor_wait()")

        self._session_check(session)
        result = None
        if session is not None and timeout is None:
            self.mtda.debug(1, "main.monitor_wait(): no timeout specified!")
            timeout = CONSTS.RPC.TIMEOUT
        if self.console_locked(session) is False and \
           self.monitor_logger is not None:
            result = self.monitor_logger.wait(what, timeout)

        self.mtda.debug(3, "main.monitor_wait(): %s" % str(result))
        return result

    def pastebin_api_key(self):
        self.mtda.debug(3, "main.pastebin_api_key()")
        return self._pastebin_api_key

    def pastebin_endpoint(self):
        self.mtda.debug(3, "main.pastebin_endpoint()")
        return self._pastebin_endpoint

    def power_locked(self, session=None):
        self.mtda.debug(3, "main.power_locked()")

        self._session_check(session)
        if self.power_controller is None:
            result = True
        else:
            result = self._check_locked(session)

        self.mtda.debug(3, "main.power_locked(): %s" % str(result))
        return result

    def _storage_event(self, status):
        self.notify("STORAGE %s" % status)

    def storage_bytes_written(self, session=None):
        self.mtda.debug(3, "main.storage_bytes_written()")

        self._session_check(session)
        result = self._writer.written

        self.mtda.debug(3, "main.storage_bytes_written(): %s" % str(result))
        return result

    def storage_compression(self, compression, session=None):
        self.mtda.debug(3, "main.storage_compression()")

        self._session_check(session)
        if self.storage_controller is None:
            result = None
        else:
            result = self._writer.compression.value
            self._writer.compression = compression

        self.mtda.debug(3, "main.storage_compression(): %s" % str(result))
        return result

    def storage_close(self, session=None):
        self.mtda.debug(3, "main.storage_close()")

        self._session_check(session)
        if self.storage_controller is None:
            result = False
        else:
            self._writer.stop()
            self._writer_data = None
            self._storage_opened = not self.storage_controller.close()
            result = (self._storage_opened is False)

        self.mtda.debug(3, "main.storage_close(): %s" % str(result))
        return result

    def storage_locked(self, session=None):
        self.mtda.debug(3, "main.storage_locked()")

        self._session_check(session)
        if self._check_locked(session):
            result = True
        # Cannot swap the shared storage device between the host and target
        # without a driver
        elif self.storage_controller is None:
            self.mtda.debug(4, "storage_locked(): no shared storage device")
            result = True
        # If hotplugging is supported, swap only if the shared storage
        # isn't opened
        elif self.storage_controller.supports_hotplug() is True:
            result = self._storage_opened
        # We also need a power controller to be safe
        elif self.power_controller is None:
            self.mtda.debug(4, "storage_locked(): no power controller")
            result = True
        # The target shall be OFF
        elif self.target_status() != "OFF":
            self.mtda.debug(4, "storage_locked(): target isn't off")
            result = True
        # Lastly, the shared storage device shall not be opened
        elif self._storage_opened is True:
            self.mtda.debug(4, "storage_locked(): "
                               "shared storage is in used (opened)")
            result = True
        # We may otherwise swap our shared storage device
        else:
            result = False

        self.mtda.debug(3, "main.storage_locked(): %s" % str(result))
        return result

    def storage_mount(self, part=None, session=None):
        self.mtda.debug(3, "main.storage_mount()")

        self._session_check(session)
        if self._storage_mounted is True:
            self.mtda.debug(4, "storage_mount(): already mounted")
            result = True
        elif self.storage_controller is None:
            self.mtda.debug(4, "storage_mount(): no shared storage device")
            return False
        else:
            result = self.storage_controller.mount(part)
            self._storage_mounted = (result is True)

        self.mtda.debug(3, "main.storage_mount(): %s" % str(result))
        return result

    def storage_update(self, dst, offset, session=None):
        self.mtda.debug(3, "main.storage_update()")

        self._session_check(session)
        result = False
        if self.storage_controller is None:
            self.mtda.debug(4, "storage_update(): no shared storage device")
        else:
            try:
                result = self.storage_controller.update(dst, offset)
                if result is True:
                    self._writer.start()
            except (FileNotFoundError, IOError) as e:
                self.mtda.debug(1, "main.storage_update(): "
                                   "%s" % str(e.args[0]))

        self.mtda.debug(3, "main.storage_update(): %s" % str(result))
        return result

    def storage_open(self, session=None):
        self.mtda.debug(3, "main.storage_open()")

        self._session_check(session)
        if self.storage_controller is None:
            self.mtda.debug(1, "storage_open(): no shared storage device")
            result = False
        else:
            self.storage_close()
            result = self.storage_controller.open()
            if result is True:
                self._writer.start()
            self._storage_opened = result

        self.mtda.debug(3, "main.storage_open(): %s" % str(result))
        return result

    def storage_status(self, session=None):
        self.mtda.debug(3, "main.storage_status()")

        self._session_check(session)
        if self.storage_controller is None:
            self.mtda.debug(4, "storage_status(): no shared storage device")
            result = "???", False, 0
        else:
            status = self.storage_controller.status()
            result = status, self._writer.writing, self._writer.written

        self.mtda.debug(3, "main.storage_status(): %s" % str(result))
        return result

    def storage_to_host(self, session=None):
        self.mtda.debug(3, "main.storage_to_host()")

        self._session_check(session)
        if self.storage_locked(session) is False:
            result = self.storage_controller.to_host()
            if result is True:
                self._storage_event(self.storage_controller.SD_ON_HOST)
        else:
            self.mtda.debug(1, "storage_to_host(): shared storage is locked")
            result = False

        self.mtda.debug(3, "main.storage_to_host(): %s" % str(result))
        return result

    def storage_to_target(self, session=None):
        self.mtda.debug(3, "main.storage_to_target()")

        self._session_check(session)
        if self.storage_locked(session) is False:
            self.storage_close()
            result = self.storage_controller.to_target()
            if result is True:
                self._storage_event(self.storage_controller.SD_ON_TARGET)
        else:
            self.mtda.debug(1, "storage_to_target(): shared storage is locked")
            result = False

        self.mtda.debug(3, "main.storage_to_target(): %s" % str(result))
        return result

    def storage_swap(self, session=None):
        self.mtda.debug(3, "main.storage_swap()")

        self._session_check(session)
        if self.storage_locked(session) is False:
            result, writing, written = self.storage_status(session)
            if result == self.storage_controller.SD_ON_HOST:
                if self.storage_controller.to_target() is True:
                    self._storage_event(self.storage_controller.SD_ON_TARGET)
            elif result == self.storage_controller.SD_ON_TARGET:
                if self.storage_controller.to_host() is True:
                    self._storage_event(self.storage_controller.SD_ON_HOST)
        result, writing, written = self.storage_status(session)
        return result

        self.mtda.debug(3, "main.storage_swap(): %s" % str(result))
        return result

    def storage_write(self, data, session=None):
        self.mtda.debug(3, "main.storage_write()")

        self._session_check(session)
        if self.storage_controller is None or self._writer.failed is True:
            result = -1
        else:
            try:
                if len(data) == 0:
                    self.mtda.debug(2, "main.storage_write(): "
                                       "using queued data")
                    data = self._writer_data
                self._writer_data = data
                self._writer.put(data, timeout=10)
                result = self.blksz
            except queue.Full:
                self.mtda.debug(2, "main.storage_write(): "
                                   "queue is full")
                result = 0

        if self._writer.failed is True:
            self.mtda.debug(1, "main.storage_write(): "
                               "write or decompression error")
            result = -1

        self.mtda.debug(3, "main.storage_write(): %s" % str(result))
        return result

    def toggle_timestamps(self):
        self.mtda.debug(3, "main.toggle_timestamps()")

        if self.console_logger is not None:
            result = self.console_logger.toggle_timestamps()
        else:
            print("no console configured/found!", file=sys.stderr)
            result = None

        self.mtda.debug(3, "main.toggle_timestamps(): %s" % str(result))
        return result

    def target_lock(self, session):
        self.mtda.debug(3, "main.target_lock()")

        self._session_check(session)
        with self._session_lock:
            owner = self.target_owner()
            if owner is None or owner == session:
                self._lock_owner = session
                self._session_event("LOCKED %s" % session)
                result = True
            else:
                result = False

        self.mtda.debug(3, "main.target_lock(): %s" % str(result))
        return result

    def target_locked(self, session):
        self.mtda.debug(3, "main.target_locked()")

        self._session_check(session)
        return self._check_locked(session)

    def target_owner(self):
        self.mtda.debug(3, "main.target_owner()")

        return self._lock_owner

    def _power_event(self, status):
        if status == self.power_controller.POWER_ON:
            self._power_expiry = 0
            self._uptime = time.monotonic()
        elif status == self.power_controller.POWER_OFF:
            self._power_expiry = None
            self._uptime = 0

        for m in self.power_monitors:
            m.power_changed(status)
        self.notify("POWER %s" % status)

    def _parse_script(self, script):
        self.mtda.debug(3, "main._parse_script()")

        result = None
        if script is not None:
            result = script.replace("... ", "    ")

        self.mtda.debug(3, "main._parse_script(): %s" % str(result))
        return result

    def exec_power_on_script(self):
        self.mtda.debug(3, "main.exec_power_on_script()")

        result = None
        if self.power_on_script:
            self.mtda.debug(4, "exec_power_on_script(): "
                               "%s" % self.power_on_script)
            result = exec(self.power_on_script,
                          {"env": self.env, "mtda": self})

        self.mtda.debug(3, "main.exec_power_on_script(): %s" % str(result))
        return result

    def _target_on(self, session=None):
        self.mtda.debug(3, "main._target_on()")

        result = False
        if self.power_locked(session) is False:
            result = self.power_controller.on()
            if result is True:
                if self.console_logger is not None:
                    self.console_logger.resume()
                self.exec_power_on_script()
                self._power_event(self.power_controller.POWER_ON)

        self.mtda.debug(3, "main._target_on(): %s" % str(result))
        return result

    def target_on(self, session=None):
        self.mtda.debug(3, "main.target_on()")

        result = True
        self._session_check(session)

        status = self.target_status()
        if status != self.power_controller.POWER_ON:
            result = False
            if self.power_locked(session) is False:
                result = self._target_on(session)

        self.mtda.debug(3, "main.target_on(): %s" % str(result))
        return result

    def exec_power_off_script(self):
        self.mtda.debug(3, "main.exec_power_off_script()")

        if self.power_off_script:
            exec(self.power_off_script, {"env": self.env, "mtda": self})

    def _target_off(self, session=None):
        self.mtda.debug(3, "main._target_off()")

        result = self.power_controller.off()
        if self.keyboard is not None:
            self.keyboard.idle()
        if self.console_logger is not None:
            self.console_logger.reset_timer()
            if result is True:
                self.console_logger.pause()
                self.exec_power_off_script()
                self._power_event(self.power_controller.POWER_OFF)

        self.mtda.debug(3, "main._target_off(): %s" % str(result))
        return result

    def target_off(self, session=None):
        self.mtda.debug(3, "main.target_off()")

        result = True
        self._session_check(session)

        status = self.target_status()
        if status != self.power_controller.POWER_OFF:
            result = False
            if self.power_locked(session) is False:
                result = self._target_off(session)

        self.mtda.debug(3, "main.target_off(): %s" % str(result))
        return result

    def target_status(self, session=None):
        self.mtda.debug(3, "main.target_status()")

        self._session_check(session)
        if self.power_controller is None:
            result = "???"
        else:
            result = self.power_controller.status()

        self.mtda.debug(3, "main.target_status(): %s" % str(result))
        return result

    def target_toggle(self, session=None):
        self.mtda.debug(3, "main.target_toggle()")

        self._session_check(session)
        if self.power_locked(session) is False:
            result = self.power_controller.toggle()
            if result == self.power_controller.POWER_ON:
                if self.console_logger is not None:
                    self.console_logger.resume()
                self.exec_power_on_script()
                self._power_event(self.power_controller.POWER_ON)
            elif result == self.power_controller.POWER_OFF:
                self.exec_power_off_script()
                if self.console_logger is not None:
                    self.console_logger.pause()
                    self.console_logger.reset_timer()
                self._power_event(self.power_controller.POWER_OFF)
        else:
            result = self.power_controller.POWER_LOCKED

        self.mtda.debug(3, "main.target_toggle(): %s" % str(result))
        return result

    def target_unlock(self, session):
        self.mtda.debug(3, "main.target_unlock()")

        result = False
        self._session_check(session)
        with self._session_lock:
            if self.target_owner() == session:
                self._session_event("UNLOCKED %s" % session)
                self._lock_owner = None
                result = True

        self.mtda.debug(3, "main.target_unlock(): %s" % str(result))
        return result

    def target_uptime(self, session=None):
        self.mtda.debug(3, "main.target_uptime()")

        result = 0
        if self._uptime > 0:
            result = time.monotonic() - self._uptime

        self.mtda.debug(3, "main.target_uptime(): %s" % str(result))
        return result

    def usb_find_by_class(self, className, session=None):
        self.mtda.debug(3, "main.usb_find_by_class()")

        self._session_check(session)
        ports = len(self.usb_switches)
        ndx = 0
        while ndx < ports:
            usb_switch = self.usb_switches[ndx]
            if usb_switch.className == className:
                return usb_switch
            ndx = ndx + 1
        return None

    def usb_has_class(self, className, session=None):
        self.mtda.debug(3, "main.usb_has_class()")

        self._session_check(session)
        usb_switch = self.usb_find_by_class(className, session)
        return usb_switch is not None

    def usb_off(self, ndx, session=None):
        self.mtda.debug(3, "main.usb_off()")

        self._session_check(session)
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                usb_switch.off()
        except IndexError:
            print("invalid USB switch #" + str(ndx), file=sys.stderr)

    def usb_off_by_class(self, className, session=None):
        self.mtda.debug(3, "main.usb_off_by_class()")

        self._session_check(session)
        usb_switch = self.usb_find_by_class(className, session)
        if usb_switch is not None:
            return usb_switch.off()
        return False

    def usb_on(self, ndx, session=None):
        self.mtda.debug(3, "main.usb_on()")

        self._session_check(session)
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                usb_switch.on()
        except IndexError:
            print("invalid USB switch #" + str(ndx), file=sys.stderr)

    def usb_on_by_class(self, className, session=None):
        self.mtda.debug(3, "main.usb_on_by_class()")

        self._session_check(session)
        usb_switch = self.usb_find_by_class(className, session)
        if usb_switch is not None:
            return usb_switch.on()
        return False

    def usb_ports(self, session=None):
        self.mtda.debug(3, "main.usb_ports()")

        self._session_check(session)
        return len(self.usb_switches)

    def usb_status(self, ndx, session=None):
        self.mtda.debug(3, "main.usb_status()")

        self._session_check(session)
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                status = usb_switch.status()
                if status == usb_switch.POWERED_OFF:
                    return "OFF"
                elif status == usb_switch.POWERED_ON:
                    return "ON"
                else:
                    return "???"
        except IndexError:
            print("invalid USB switch #" + str(ndx), file=sys.stderr)
            return "ERR"
        return "???"

    def usb_toggle(self, ndx, session=None):
        self.mtda.debug(3, "main.usb_toggle()")

        self._session_check(session)
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                usb_switch.toggle()
        except IndexError:
            print("invalid USB switch #" + str(ndx), file=sys.stderr)

    def video_url(self, host="", opts=None):
        self.mtda.debug(3, "main.video_url(host={0}, "
                           "opts={1})".format(host, opts))

        result = None
        if self.video is not None:
            result = self.video.url(host, opts)

        self.mtda.debug(3, "main.video_url(): %s" % str(result))
        return result

    def load_config(self, remote=None, is_server=False):
        self.mtda.debug(3, "main.load_config()")

        self.remote = remote
        self.is_remote = remote is not None
        self.is_server = is_server
        parser = configparser.ConfigParser()
        configs_found = parser.read(self.config_files)
        if configs_found is False:
            return

        if parser.has_section('main'):
            self.load_main_config(parser)
        if parser.has_section('pastebin'):
            self.load_pastebin_config(parser)
        if parser.has_section('remote'):
            self.load_remote_config(parser)
        self.load_timeouts_config(parser)
        if parser.has_section('ui'):
            self.load_ui_config(parser)
        if self.is_remote is False and is_server is True:
            if parser.has_section('assistant'):
                self.load_assistant_config(parser)
            if parser.has_section('environment'):
                self.load_environment(parser)
            if parser.has_section('power'):
                self.load_power_config(parser)
            if parser.has_section('console'):
                self.load_console_config(parser)
            if parser.has_section('keyboard'):
                self.load_keyboard_config(parser)
            if parser.has_section('monitor'):
                self.load_monitor_config(parser)
            if parser.has_section('storage'):
                self.load_storage_config(parser)
            if parser.has_section('usb'):
                self.load_usb_config(parser)
            if parser.has_section('video'):
                self.load_video_config(parser)
            if parser.has_section('scripts'):
                scripts = parser['scripts']
                self.power_on_script = self._parse_script(
                    scripts.get('power on', None))
                self.power_off_script = self._parse_script(
                    scripts.get('power off', None))

    def load_main_config(self, parser):
        self.mtda.debug(3, "main.load_main_config()")

        # Name of this agent
        self.name = parser.get('main', 'name', fallback=self.name)

        self.mtda.debug_level = int(
            parser.get('main', 'debug', fallback=self.mtda.debug_level))
        self.mtda.fuse = parser.getboolean(
            'main', 'fuse', fallback=self.mtda.fuse)

    def load_environment(self, parser):
        self.mtda.debug(3, "main.load_environment()")

        for opt in parser.options('environment'):
            value = parser.get('environment', opt)
            self.mtda.debug(4, "main.load_environment(): "
                               "%s => %s" % (opt, value))
            self.env_set(opt, value)

    def load_assistant_config(self, parser):
        self.mtda.debug(3, "main.load_assistant_config()")

        try:
            # Get variant
            variant = parser.get('assistant', 'variant')
            # Try loading its support class
            mod = importlib.import_module("mtda.assistant." + variant)
            factory = getattr(mod, 'instantiate')
            self.assistant = factory(self)
            self.assistant.variant = variant
            # Configure the assistant
            self.assistant.configure(dict(parser.items('assistant')))
        except configparser.NoOptionError:
            print('assistant variant not defined!', file=sys.stderr)
        except ImportError:
            print('assistant "%s" could not be found/loaded!' % (
                variant), file=sys.stderr)

    def load_console_config(self, parser):
        self.mtda.debug(3, "main.load_console_config()")

        try:
            # Get variant
            variant = parser.get('console', 'variant')
            # Try loading its support class
            mod = importlib.import_module("mtda.console." + variant)
            factory = getattr(mod, 'instantiate')
            self.console = factory(self)
            self.console.variant = variant
            # Configure the console
            config = dict(parser.items('console'))
            self.console.configure(config)
            timestamps = parser.getboolean('console', 'timestamps',
                                           fallback=None)
            self._time_from_pwr = timestamps
            if timestamps is None or timestamps is True:
                # check 'time-from' / 'time-until' settings if timestamps is
                # either yes or unspecified
                if 'time-until' in config:
                    self._time_until_str = config['time-until']
                    self._time_from_pwr = True
                if 'time-from' in config:
                    self._time_from_str = config['time-from']
                    self._time_from_pwr = False
        except configparser.NoOptionError:
            print('console variant not defined!', file=sys.stderr)
        except ImportError:
            print('console "%s" could not be found/loaded!' % (
                variant), file=sys.stderr)

    def load_keyboard_config(self, parser):
        self.mtda.debug(3, "main.load_keyboard_config()")

        try:
            # Get variant
            variant = parser.get('keyboard', 'variant')
            # Try loading its support class
            mod = importlib.import_module("mtda.keyboard." + variant)
            factory = getattr(mod, 'instantiate')
            self.keyboard = factory(self)
            # Configure the keyboard controller
            self.keyboard.configure(dict(parser.items('keyboard')))
        except configparser.NoOptionError:
            print('keyboard controller variant not defined!', file=sys.stderr)
        except ImportError:
            print('keyboard controller "%s" could not be found/loaded!' % (
                variant), file=sys.stderr)

    def load_monitor_config(self, parser):
        self.mtda.debug(3, "main.load_monitor_config()")

        try:
            # Get variant
            variant = parser.get('monitor', 'variant')
            # Try loading its support class
            mod = importlib.import_module("mtda.console." + variant)
            factory = getattr(mod, 'instantiate')
            self.monitor = factory(self)
            self.monitor.variant = variant
            # Configure the monitor console
            self.monitor.configure(dict(parser.items('monitor')))
        except configparser.NoOptionError:
            print('monitor variant not defined!', file=sys.stderr)
        except ImportError:
            print('monitor "%s" could not be found/loaded!' % (
                variant), file=sys.stderr)

    def load_pastebin_config(self, parser):
        self.mtda.debug(3, "main.load_pastebin_config()")
        self._pastebin_api_key = parser.get('pastebin', 'api-key',
                                            fallback='')
        self._pastebin_endpoint = parser.get('pastebin', 'endpoint',
                                             fallback=DEFAULT_PASTEBIN_EP)

    def load_power_config(self, parser):
        self.mtda.debug(3, "main.load_power_config()")

        try:
            # Get variant
            variant = parser.get('power', 'variant')
            # Try loading its support class
            mod = importlib.import_module("mtda.power." + variant)
            factory = getattr(mod, 'instantiate')
            self.power_controller = factory(self)
            self.power_controller.variant = variant
            # Configure the power controller
            self.power_controller.configure(dict(parser.items('power')))
        except configparser.NoOptionError:
            print('power controller variant not defined!', file=sys.stderr)
        except ImportError:
            print('power controller "%s" could not be found/loaded!' % (
                variant), file=sys.stderr)

    def load_storage_config(self, parser):
        self.mtda.debug(3, "main.load_storage_config()")

        try:
            # Get variant
            variant = parser.get('storage', 'variant')
            # Try loading its support class
            mod = importlib.import_module("mtda.storage." + variant)
            factory = getattr(mod, 'instantiate')
            self.storage_controller = factory(self)
            self._writer = AsyncImageWriter(self, self.storage_controller)
            # Configure the storage controller
            self.storage_controller.configure(dict(parser.items('storage')))
        except configparser.NoOptionError:
            print('storage controller variant not defined!', file=sys.stderr)
        except ImportError:
            print('power controller "%s" could not be found/loaded!' % (
                variant), file=sys.stderr)

    def load_remote_config(self, parser):
        self.mtda.debug(3, "main.load_remote_config()")

        self.conport = int(
            parser.get('remote', 'console', fallback=self.conport))
        self.ctrlport = int(
            parser.get('remote', 'control', fallback=self.ctrlport))
        if self.is_server is False:
            if self.remote is None:
                # Load remote setting from the configuration
                self.remote = parser.get(
                    'remote', 'host', fallback=self.remote)
                # Allow override from the environment
                self.remote = os.getenv('MTDA_REMOTE', self.remote)

            # Attempt to resolve remote using Zeroconf
            watcher = mtda.discovery.Watcher(CONSTS.MDNS.TYPE)
            ip = watcher.lookup(self.remote)
            if ip is not None:
                self.debug(2, "resolved '{}' ({}) "
                              "using Zeroconf".format(self.remote, ip))
                self.remote = ip
        else:
            self.remote = None
        self.is_remote = self.remote is not None

    def load_timeouts_config(self, parser):
        self.mtda.debug(3, "main.load_timeouts_config()")

        result = None
        s = "timeouts"

        self._lock_timeout = int(parser.get(s, "lock",
                                 fallback=CONSTS.DEFAULTS.LOCK_TIMEOUT))
        self._power_timeout = int(parser.get(s, "power",
                                  fallback=CONSTS.DEFAULTS.POWER_TIMEOUT))
        self._session_timeout = int(parser.get(s, "session",
                                    fallback=CONSTS.DEFAULTS.SESSION_TIMEOUT))

        self.mtda.debug(3, "main.load_timeouts_config: %s" % str(result))
        return result

    def load_ui_config(self, parser):
        self.mtda.debug(3, "main.load_ui_config()")
        self.prefix_key = self._prefix_key_code(parser.get(
            'ui', 'prefix', fallback=DEFAULT_PREFIX_KEY))

    def load_usb_config(self, parser):
        self.mtda.debug(3, "main.load_usb_config()")

        try:
            # Get number of ports
            usb_ports = int(parser.get('usb', 'ports'))
            for port in range(0, usb_ports):
                port = port + 1
                section = "usb" + str(port)
                if parser.has_section(section):
                    self.load_usb_port_config(parser, section)
        except configparser.NoOptionError:
            usb_ports = 0

    def load_usb_port_config(self, parser, section):
        self.mtda.debug(3, "main.load_usb_port_config()")

        try:
            # Get attributes
            className = parser.get(section, 'class', fallback="")
            variant = parser.get(section, 'variant')

            # Try loading its support class
            mod = importlib.import_module("mtda.usb." + variant)
            factory = getattr(mod, 'instantiate')
            usb_switch = factory(self)

            # Configure and probe the USB switch
            usb_switch.configure(dict(parser.items(section)))
            usb_switch.probe()

            # Store other attributes
            usb_switch.className = className

            # Add this USB switch
            self.usb_switches.append(usb_switch)
        except configparser.NoOptionError:
            print('usb switch variant not defined!', file=sys.stderr)
        except ImportError:
            print('usb switch "%s" could not be found/loaded!' % (
                variant), file=sys.stderr)

    def load_video_config(self, parser):
        self.mtda.debug(3, "main.load_video_config()")

        try:
            # Get variant
            variant = parser.get('video', 'variant')
            # Try loading its support class
            mod = importlib.import_module("mtda.video." + variant)
            factory = getattr(mod, 'instantiate')
            self.video = factory(self)
            # Configure the video controller
            self.video.configure(dict(parser.items('video')))
        except configparser.NoOptionError:
            print('video controller variant not defined!', file=sys.stderr)
        except ImportError:
            print('video controller "%s" could not be found/loaded!' % (
                variant), file=sys.stderr)

    def notify(self, what):
        self.mtda.debug(3, "main.notify({})".format(what))

        result = None
        if self.socket is not None:
            self.socket.send(CONSTS.CHANNEL.EVENTS, flags=zmq.SNDMORE)
            self.socket.send_string(what)

        self.mtda.debug(3, "main.notify: %s" % str(result))
        return result

    def start(self):
        self.mtda.debug(3, "main.start()")

        if self.is_remote is True:
            return True

        # Probe the specified power controller
        if self.power_controller is not None:
            status = self.power_controller.probe()
            if status is False:
                print('Probe of the Power Controller failed!', file=sys.stderr)
                return False

        # Probe the specified storage controller
        if self.storage_controller is not None:
            status = self.storage_controller.probe()
            if status is False:
                print('Probe of the shared storage device failed!',
                      file=sys.stderr)
                return False

        if self.console is not None:
            # Create a publisher
            if self.is_server is True:
                context = zmq.Context()
                socket = context.socket(zmq.PUB)
                socket.bind("tcp://*:%s" % self.conport)
            else:
                socket = None
            self.socket = socket

            # Create and start console logger
            status = self.console.probe()
            if status is False:
                print('Probe of the %s console failed!' % (
                      self.console.variant), file=sys.stderr)
                return False
            self.console_logger = ConsoleLogger(
                self, self.console, socket, self.power_controller, b'CON')
            if self._time_from_str is not None:
                self.console_logger.time_from = self._time_from_str
            if self._time_until_str is not None:
                self.console_logger.time_until = self._time_until_str
            if self._time_from_pwr is not None and self._time_from_pwr is True:
                self.toggle_timestamps()
            self.console_logger.start()

        if self.monitor is not None:
            # Create and start console logger
            status = self.monitor.probe()
            if status is False:
                print('Probe of the %s monitor console failed!' % (
                      self.monitor.variant), file=sys.stderr)
                return False
            self.monitor_logger = ConsoleLogger(
                self, self.monitor, socket, self.power_controller, b'MON')
            self.monitor_logger.start()

        if self.keyboard is not None:
            status = self.keyboard.probe()
            if status is False:
                print('Probe of the %s keyboard failed!' % (
                      self.keyboard.variant), file=sys.stderr)
                return False

        if self.assistant is not None:
            self.power_monitors.append(self.assistant)
            self.assistant.start()

        if self.video is not None:
            status = self.video.probe()
            if status is False:
                print('Probe of the %s video failed!' % (
                      self.video.variant), file=sys.stderr)
                return False
            self.video.start()

        if self.is_server is True:
            self._session_timer = mtda.utils.RepeatTimer(60,
                                                         self._session_check)
            self._session_timer.start()

        return True

    def stop(self):
        self.mtda.debug(3, "main.stop()")

        if self.is_remote is True:
            return True

        # stop sesssion timer
        self._session_timer.cancel()

        # stop video
        if self.video is not None:
            self.video.stop()

        # stop assistant
        if self.assistant is not None:
            self.power_monitors.remove(self.assistant)
            self.assistant.stop()

        # stop monitor console
        if self.monitor is not None:
            self.monitor_logger.stop()

        # stop main console
        if self.console is not None:
            self.console_logger.stop()

        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def _session_check(self, session=None):
        self.mtda.debug(3, "main._session_check(%s)" % str(session))

        events = []
        now = time.monotonic()
        power_off = False
        result = None

        with self._session_lock:
            # Register new session
            if session is not None:
                if session not in self._sessions:
                    events.append("ACTIVE %s" % session)
                self._sessions[session] = now + (self._session_timeout * 60)

            # Check for inactive sessions
            inactive = []
            for s in self._sessions:
                left = self._sessions[s] - now
                self.mtda.debug(2, "session %s: %d seconds" % (s, left))
                if left <= 0:
                    inactive.append(s)
            for s in inactive:
                events.append("INACTIVE %s" % s)
                self._sessions.pop(s, "")

                # Check if we should arm the auto power-off timer
                if (self._power_expiry is not None and
                        self._power_timeout > 0 and
                        len(self._sessions) == 0):

                    self.mtda.debug(2, "device will be powered down in %d "
                                       "minutes" % self._power_timeout)
                    self._power_expiry = now + (self._power_timeout * 60)

            if len(self._sessions) == 0:
                if self._power_expiry is not None and now > self._power_expiry:
                    self._lock_expiry = 0
                    power_off = True

            # Release device if the session owning the lock is idle
            if self._lock_owner is not None:
                if session == self._lock_owner:
                    self._lock_expiry = now + (self._lock_timeout * 60)
                elif now >= self._lock_expiry:
                    events.append("UNLOCKED %s" % self._lock_owner)
                    self._lock_owner = None

        # Send event sessions generated above
        for e in events:
            self._session_event(e)

        # Check if we should auto power-off the device
        if power_off is True:
            self._target_off()
            self.mtda.debug(2, "device powered down after %d minutes of "
                               "inactivity" % self._power_timeout)

        self.mtda.debug(3, "main._session_check: %s" % str(result))
        return result

    def _session_event(self, info):
        self.mtda.debug(3, "main._session_event(%s)" % str(info))

        result = None
        if info is not None:
            self.notify("SESSION %s" % info)

        self.mtda.debug(3, "main._session_event: %s" % str(result))
        return result

    def _check_locked(self, session):
        self.mtda.debug(3, "main._check_locked()")

        owner = self.target_owner()
        if owner is None:
            return False
        status = False if session == owner else True
        return status
