# ---------------------------------------------------------------------------
# MTDA main
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2023 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import configparser
import gevent
import glob
import importlib
import os
import queue
import shutil
import socket
import subprocess
import sys
import threading
import tempfile
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
import mtda.scripts
import mtda.video.controller
import mtda.utils
from mtda import __version__
from mtda.support.usb import Composite

try:
    www_support = True
    import mtda.www
except ModuleNotFoundError:
    www_support = False


DEFAULT_PREFIX_KEY = 'ctrl-a'
DEFAULT_PASTEBIN_EP = "http://pastebin.com/api/api_post.php"


def _make_printable(s):
    return s.encode('ascii', 'replace').decode()


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
        self.power = None
        self.power_on_script = None
        self.power_off_script = None
        self.power_monitors = []
        self.storage = None
        self._pastebin_api_key = None
        self._pastebin_endpoint = None
        self._storage_mounted = False
        self._storage_opened = False
        self._storage_owner = None
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
        self._power_lock = threading.Lock()
        self._session_lock = threading.Lock()
        self._session_timer = None
        self._sessions = {}
        self._socket_lock = threading.Lock()
        self._time_from_pwr = None
        self._time_from_str = None
        self._time_until_str = None
        self._uptime = 0
        self.version = __version__
        self._www = None

        # Config file in /etc/mtda/config
        if os.path.exists('/etc/mtda'):
            self.config_files.append(os.path.join('/etc', 'mtda', 'config'))

        # Config fragments in /etc/mtda/config.d/
        if os.path.exists('/etc/mtda/config.d'):
            fragments = glob.glob('/etc/mtda/config.d/*.conf')
            if len(fragments) > 0:
                self.config_files.extend(sorted(fragments))

        # Config file in $HOME/.mtda/config
        home = os.getenv('HOME', '')
        if home != '':
            self.config_files.append(os.path.join(home, '.mtda', 'config'))

    def agent_version(self):
        return self.version

    def command(self, args, session=None):
        self.mtda.debug(3, "main.command()")

        self._session_check(session)
        result = False
        if self.power_locked(session) is False:
            result = self.power.command(args)

        self.mtda.debug(3, "main.command(): %s" % str(result))
        return result

    def _composite_start(self):
        self.mtda.debug(3, "main._composite_start()")

        result = True
        storage = self.storage
        if storage is not None and storage.variant == 'usbf':
            status, _, _ = self.storage_status()
            enabled = status == CONSTS.STORAGE.ON_TARGET
            self.mtda.debug(3, "main._composite_start(): "
                               "with storage? {}".format(enabled))
            Composite.storage_toggle(enabled)
            result = Composite.install()
        elif self.keyboard is not None:
            result = Composite.install()

        self.mtda.debug(3, "main._composite_start(): {}".format(result))
        return result

    def _composite_stop(self):
        self.mtda.debug(3, "main._composite_stop()")

        result = None
        storage = self.storage
        if storage is not None and storage.variant == 'usbf':
            Composite.remove()

        self.mtda.debug(3, "main._composite_stop(): {}".format(result))
        return result

    def config_set_power_timeout(self, timeout, session=None):
        self.mtda.debug(3, "main.config_set_power_timeout()")

        result = self._power_timeout
        self._power_timeout = timeout
        if timeout == 0:
            self._power_expiry = None
        self._session_check()

        self.mtda.debug(3, "main.config_set_power_timeout(): "
                           "{}".format(result))
        return result

    def config_set_session_timeout(self, timeout, session=None):
        self.mtda.debug(3, "main.config_set_session_timeout()")

        if timeout < CONSTS.SESSION.MIN_TIMEOUT:
            timeout = CONSTS.SESSION.MIN_TIMEOUT

        result = self._session_timeout
        self._session_timeout = timeout

        with self._session_lock:
            now = time.monotonic()
            for s in self._sessions:
                left = self._sessions[s] - now
                if left > timeout:
                    self._sessions[s] = now + timeout
        self._session_check()

        self.mtda.debug(3, "main.config_set_session_timeout(): "
                           "{}".format(result))
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
        result = 0
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
            timeout = CONSTS.RPC.TIMEOUT
            self.warn('console_wait() without timeout, '
                      'using default ({})'.format(timeout))
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

    def warn(self, msg):
        print('warning: {}'.format(msg), file=sys.stderr)

    def error(self, msg):
        print('error: {}'.format(msg), file=sys.stderr)

    def env_get(self, name, default=None, session=None):
        self.mtda.debug(3, "env_get()")

        result = default
        if name in self.env:
            result = self.env[name]

        self.mtda.debug(3, "env_get(): %s" % str(result))
        return result

    def env_set(self, name, value, session=None):
        self.mtda.debug(3, "env_set()")

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
            timeout = CONSTS.RPC.TIMEOUT
            self.warn('monitor_wait() called without timeout, '
                      'using default({})'.format(timeout))
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
        if self.power is None:
            result = True
        else:
            result = self._check_locked(session)

        self.mtda.debug(3, "main.power_locked(): %s" % str(result))
        return result

    def publish(self, topic, data):
        if self.socket is not None:
            with self._socket_lock:
                self.socket.send(topic, flags=zmq.SNDMORE)
                self.socket.send(data)

    def _storage_event(self, status):
        self.notify(CONSTS.EVENTS.STORAGE, status)

    def storage_bytes_written(self, session=None):
        self.mtda.debug(3, "main.storage_bytes_written()")

        self._session_check(session)
        result = self._writer.written

        self.mtda.debug(3, "main.storage_bytes_written(): %s" % str(result))
        return result

    def storage_compression(self, compression, session=None):
        self.mtda.debug(3, "main.storage_compression()")

        self._session_check(session)
        if self.storage is None:
            result = None
        else:
            result = self._writer.compression.value
            self._writer.compression = compression

        self.mtda.debug(3, "main.storage_compression(): %s" % str(result))
        return result

    def storage_bmap_dict(self, bmapDict, session=None):
        self.mtda.debug(3, "main.storage_bmap_dict()")

        self._session_check(session)
        if self.storage is None:
            result = None
        else:
            self.storage.setBmap(bmapDict)
            result = True
        self.mtda.debug(3, "main.storage_bmap_dict()(): %s" % str(result))

    def storage_close(self, session=None):
        self.mtda.debug(3, "main.storage_close()")

        self._session_check(session)
        if self.storage is None:
            result = False
        else:
            self._writer.stop()
            self._writer_data = None
            self._storage_opened = not self.storage.close()
            self._storage_owner = None
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
        elif self.storage is None:
            self.mtda.debug(4, "storage_locked(): no shared storage device")
            result = True
        # If hotplugging is supported, swap only if the shared storage
        # isn't opened
        elif self.storage.supports_hotplug() is True:
            result = self._storage_opened
        # We also need a power controller to be safe
        elif self.power is None:
            self.mtda.debug(4, "storage_locked(): no power controller")
            result = True
        # The target shall be OFF
        elif self.target_status() != "OFF":
            self.mtda.debug(4, "storage_locked(): target isn't off")
            result = True
        # Lastly, the shared storage device shall not be opened
        elif self._storage_opened is True:
            self.mtda.debug(4, "storage_locked(): "
                               "shared storage is in use (opened)")
            result = True
        # We may otherwise swap our shared storage device
        else:
            result = False

        self.mtda.debug(3, "main.storage_locked(): %s" % str(result))
        return result

    def storage_mount(self, part=None, session=None):
        self.mtda.debug(3, "main.storage_mount()")

        self._session_check(session)
        if self.storage_controller.static_is_mounted is True:
            self.mtda.debug(4, "storage_mount(): already mounted")
            result = True
        elif self.storage is None:
            self.mtda.debug(4, "storage_mount(): no shared storage device")
            return False
        else:
            result = self.storage.mount(part)
            self._storage_mounted = (result is True)

        self.mtda.debug(3, "main.storage_mount(): %s" % str(result))
        return result

    def storage_update(self, dst, offset, session=None):
        self.mtda.debug(3, "main.storage_update()")

        self._session_check(session)
        result = False
        if self.storage is None:
            self.mtda.debug(4, "storage_update(): no shared storage device")
        else:
            try:
                result = self.storage.update(dst, offset)
            except (FileNotFoundError, IOError) as e:
                self.mtda.debug(1, "main.storage_update(): "
                                   "%s" % str(e.args[0]))

        self.mtda.debug(3, "main.storage_update(): %s" % str(result))
        return result

    def storage_open(self, session=None):
        self.mtda.debug(3, 'main.storage_open()')

        self._session_check(session)
        owner = self._storage_owner
        status, _, _ = self.storage_status()

        if self.storage is None:
            raise RuntimeError('no shared storage device')
        elif status != CONSTS.STORAGE.ON_HOST:
            raise RuntimeError('shared storage not attached to host')
        elif owner is not None and owner != session:
            raise RuntimeError('shared storage in use')
        elif self._storage_opened is False:
            self.storage.open()
            self._storage_opened = True
            self._storage_owner = session
            self._writer.start()

        self.mtda.debug(3, 'main.storage_open(): success')

    def storage_status(self, session=None):
        self.mtda.debug(3, "main.storage_status()")

        self._session_check(session)
        if self.storage is None:
            self.mtda.debug(4, "storage_status(): no shared storage device")
            result = CONSTS.STORAGE.UNKNOWN, False, 0
        else:
            # avoid costly query of storage state when we know it anyways
            status = CONSTS.STORAGE.ON_HOST \
                if self._writer.writing else self.storage.status()
            result = status, self._writer.writing, self._writer.written

        self.mtda.debug(3, "main.storage_status(): %s" % str(result))
        return result

    def storage_to_host(self, session=None):
        self.mtda.debug(3, "main.storage_to_host()")

        self._session_check(session)
        if self.storage_locked(session) is False:
            result = self.storage.to_host()
            if result is True:
                self._storage_event(CONSTS.STORAGE.ON_HOST)
        else:
            self.error('cannot switch storage to host: locked')
            result = False

        self.mtda.debug(3, "main.storage_to_host(): %s" % str(result))
        return result

    def storage_to_target(self, session=None):
        self.mtda.debug(3, "main.storage_to_target()")

        self._session_check(session)
        if self.storage_locked(session) is False:
            self.storage_close()
            result = self.storage.to_target()
            if result is True:
                self._storage_event(CONSTS.STORAGE.ON_TARGET)
        else:
            self.error('cannot switch storage to target: locked')
            result = False

        self.mtda.debug(3, "main.storage_to_target(): %s" % str(result))
        return result

    def storage_swap(self, session=None):
        self.mtda.debug(3, "main.storage_swap()")

        self._session_check(session)
        if self.storage_locked(session) is False:
            result, writing, written = self.storage_status(session)
            if result == CONSTS.STORAGE.ON_HOST:
                if self.storage.to_target() is True:
                    self._storage_event(CONSTS.STORAGE.ON_TARGET)
            elif result == CONSTS.STORAGE.ON_TARGET:
                if self.storage.to_host() is True:
                    self._storage_event(CONSTS.STORAGE.ON_HOST)
        result, writing, written = self.storage_status(session)
        return result

        self.mtda.debug(3, "main.storage_swap(): %s" % str(result))
        return result

    def storage_write(self, data, session=None):
        self.mtda.debug(3, "main.storage_write()")

        self._session_check(session)
        if self.storage is None:
            raise RuntimeError('no shared storage')
        elif self._storage_opened is False:
            raise RuntimeError('shared storage was not opened')
        elif self._writer.failed is True:
            raise RuntimeError('write or decompression error '
                               'from shared storage')
        elif session != self._storage_owner:
            raise RuntimeError('shared storage in use')

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
            self.error('storage_write failed: write or decompression error')
            result = -1

        self.mtda.debug(3, "main.storage_write(): %s" % str(result))
        return result

    def systemd_configure(self):
        from filecmp import dircmp

        console = self.console
        storage = self.storage
        video = self.video

        with tempfile.TemporaryDirectory() as newdir:

            # make drivers generate their systemd dropins in a temporary
            # directory
            if console is not None and hasattr(console, 'configure_systemd'):
                console.configure_systemd(newdir)
            if storage is not None and hasattr(storage, 'configure_systemd'):
                storage.configure_systemd(newdir)
            if video is not None and hasattr(video, 'configure_systemd'):
                video.configure_systemd(newdir)

            # make sure target directory exists
            etcdir = '/etc/systemd/system/mtda.service.d/'
            os.makedirs(etcdir, exist_ok=True)

            # check for changes between the target directory and the
            # temporary directory to determine if systemd should be
            # reloaded
            dcmp = dircmp(etcdir, newdir)
            diffs = len(dcmp.left_only)    # files that were removed
            diffs += len(dcmp.right_only)  # files that were added
            diffs += len(dcmp.diff_files)  # files that were changed
            if diffs > 0:
                self.mtda.debug(1, "main.systemd_configure(): "
                                   "installing new systemd dropins")
                shutil.rmtree(etcdir)
                shutil.copytree(newdir, etcdir)
                subprocess.call(['systemctl', 'daemon-reload'])
            else:
                self.mtda.debug(2, "main.systemd_configure(): "
                                   "no changes to systemd dropins")

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
        self._power_expiry = None
        if status == CONSTS.POWER.ON:
            self._uptime = time.monotonic()
        elif status == CONSTS.POWER.OFF:
            self._uptime = 0

        for m in self.power_monitors:
            m.power_changed(status)
        self.notify(CONSTS.EVENTS.POWER, status)

    def _env_for_script(self):
        variant = 'unknown'
        if 'variant' in self.env:
            variant = self.env['variant']
        return {
            "env": self.env,
            "mtda": self,
            "scripts": mtda.scripts,
            "sleep": gevent.sleep,
            "variant": variant
        }

    def _load_device_scripts(self):
        env = self._env_for_script()
        mtda.scripts.load_device_scripts(env['variant'], env)
        for e in env.keys():
            setattr(mtda.scripts, e, env[e])

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
            env = self._env_for_script()
            result = exec(self.power_on_script, env)

        self.mtda.debug(3, "main.exec_power_on_script(): %s" % str(result))
        return result

    def _target_on(self, session=None):
        self.mtda.debug(3, "main._target_on()")

        result = False
        if self.power_locked(session) is False:
            # Toggle the mass storage functions of the usbf controller
            result = self._composite_start()

            # Turn the DUT on
            if result is True:
                result = self.power.on()

            # Resume logging
            if result is True:
                if self.console_logger is not None:
                    self.console_logger.resume()
                if self.monitor_logger is not None:
                    self.monitor_logger.resume()

                # user-provided power-on script may now be executed
                # (target is up and logging running)
                #
                # power sequence:
                #   <power-on>
                #     <power-on-script>
                #       <runtime>
                #     <power-off-script>
                #   <power-off>
                #
                self.exec_power_on_script()

                self._power_event(CONSTS.POWER.ON)

        self.mtda.debug(3, "main._target_on(): {}".format(result))
        return result

    def target_on(self, session=None):
        self.mtda.debug(3, "main.target_on()")

        result = True
        self._session_check(session)
        with self._power_lock:
            status = self._target_status()
            if status != CONSTS.POWER.ON:
                result = False
                if self.power_locked(session) is False:
                    result = self._target_on(session)

        self.mtda.debug(3, "main.target_on(): {}".format(result))
        return result

    def exec_power_off_script(self):
        self.mtda.debug(3, "main.exec_power_off_script()")

        if self.power_off_script:
            env = self._env_for_script()
            exec(self.power_off_script, env)

    def _target_off(self, session=None):
        self.mtda.debug(3, "main._target_off()")

        # call power-off script before anything else
        #
        # power sequence:
        #   <power-on>
        #     <power-on-script>
        #       <runtime>
        #     <power-off-script>
        #   <power-off>
        #
        self.exec_power_off_script()

        # pause console
        if self.console_logger is not None:
            self.console_logger.reset_timer()
            self.console_logger.pause()

        # and monitor
        if self.monitor_logger is not None:
            self.monitor_logger.reset_timer()
            self.monitor_logger.pause()

        # release keyboard
        if self.keyboard is not None:
            self.keyboard.idle()

        result = True
        if self.power is not None:
            result = self.power.off()
        self._composite_stop()
        self._power_event(CONSTS.POWER.OFF)

        self.mtda.debug(3, "main._target_off(): {}".format(result))
        return result

    def target_off(self, session=None):
        self.mtda.debug(3, "main.target_off()")

        result = True
        self._session_check(session)
        with self._power_lock:
            status = self._target_status()
            if status != CONSTS.POWER.OFF:
                result = False
                if self.power_locked(session) is False:
                    result = self._target_off(session)

        self.mtda.debug(3, "main.target_off(): {}".format(result))
        return result

    def _target_status(self, session=None):
        self.mtda.debug(3, "main._target_status()")

        if self.power is None:
            result = CONSTS.POWER.UNSURE
        else:
            result = self.power.status()

        self.mtda.debug(3, "main._target_status(): {}".format(result))
        return result

    def target_status(self, session=None):
        self.mtda.debug(3, "main.target_status()")

        with self._power_lock:
            result = self._target_status(session)

        self.mtda.debug(3, "main.target_status(): {}".format(result))
        return result

    def target_toggle(self, session=None):
        self.mtda.debug(3, "main.target_toggle()")

        result = CONSTS.POWER.UNSURE
        self._session_check(session)
        with self._power_lock:
            if self.power_locked(session) is False:
                status = self._target_status(session)
                if status == CONSTS.POWER.OFF:
                    if self._target_on() is True:
                        result = CONSTS.POWER.ON
                elif status == CONSTS.POWER.ON:
                    if self._target_off() is True:
                        result = CONSTS.POWER.OFF
            else:
                result = CONSTS.POWER.LOCKED

        self.mtda.debug(3, "main.target_toggle(): {}".format(result))
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

    def load_config(self, remote=None, is_server=False, config_files=None):
        self.mtda.debug(3, "main.load_config()")

        if config_files is None:
            config_files = os.getenv('MTDA_CONFIG', self.config_files)

        self.mtda.debug(2, "main.load_config(): "
                           "config_files={}".format(config_files))

        self.remote = os.getenv('MTDA_REMOTE', remote)
        self.is_remote = remote is not None
        self.is_server = is_server
        parser = configparser.ConfigParser()
        configs_found = parser.read(config_files)
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
            # load and configure core sub-systems
            subsystems = ['power', 'console', 'storage', 'monitor', 'keyboard',
                          'video']
            for sub in subsystems:
                if parser.has_section(sub):
                    try:
                        postconf = None
                        hook = 'post_configure_{}'.format(sub)
                        if hasattr(self, hook):
                            postconf = getattr(self, hook)
                        self.load_subsystem(sub, parser, postconf)
                    except configparser.NoOptionError:
                        self.error("variant not defined for '{}'!".format(sub))
                    except ImportError:
                        self.error("{} could not be found/loaded!".format(sub))
            # configure additional components
            if parser.has_section('environment'):
                self.load_environment(parser)
            if parser.has_section('usb'):
                self.load_usb_config(parser)
            if parser.has_section('scripts'):
                scripts = parser['scripts']
                self.power_on_script = self._parse_script(
                    scripts.get('power on', None))
                self.power_off_script = self._parse_script(
                    scripts.get('power off', None))
            else:
                self.power_on_script = self._parse_script(
                    "scripts.power_on()")
                self.power_off_script = self._parse_script(
                    "scripts.power_off()")
            self._load_device_scripts()

            # web-base UI
            if www_support is True:
                self._www = mtda.www.Service(self)
                if parser.has_section('www'):
                    self.load_www_config(parser)

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

    def load_subsystem(self, subsystem, parser, postconf=None):
        variant = parser.get(subsystem, 'variant')
        mod = importlib.import_module("mtda.{}.{}".format(subsystem, variant))
        factory = getattr(mod, 'instantiate')
        instance = factory(self)
        setattr(self, subsystem, instance)
        setattr(instance, 'variant', variant)
        config = dict(parser.items(subsystem))
        if hasattr(instance, 'configure'):
            instance.configure(dict(parser.items(subsystem)))
        if postconf is not None:
            postconf(instance, config, parser)
        return instance, config

    def post_configure_console(self, console, config, parser):
        self.mtda.debug(3, "main.post_configure_console()")

        timestamps = parser.getboolean('console', 'timestamps', fallback=None)
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

    def load_pastebin_config(self, parser):
        self.mtda.debug(3, "main.load_pastebin_config()")
        self._pastebin_api_key = parser.get('pastebin', 'api-key',
                                            fallback='')
        self._pastebin_endpoint = parser.get('pastebin', 'endpoint',
                                             fallback=DEFAULT_PASTEBIN_EP)

    def post_configure_storage(self, storage, config, parser):
        self.mtda.debug(3, "main.post_configure_storage()")
        self._writer = AsyncImageWriter(self, storage)

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

        self._lock_timeout = self._lock_timeout * 60
        self._power_timeout = self._power_timeout * 60
        self._session_timeout = self._session_timeout * 60

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

    def load_www_config(self, parser):
        self.mtda.debug(3, "main.load_www_config()")

        if www_support is True:
            self._www.configure(dict(parser.items('www')))

    def notify(self, what, info):
        self.mtda.debug(3, "main.notify({},{})".format(what, info))

        result = None
        if self.socket is not None:
            with self._socket_lock:
                self.socket.send(CONSTS.CHANNEL.EVENTS, flags=zmq.SNDMORE)
                self.socket.send_string("{} {}".format(what, info))
        if self._www is not None:
            self._www.notify(what, info)

        self.mtda.debug(3, "main.notify: {}".format(result))
        return result

    def start(self):
        self.mtda.debug(3, "main.start()")

        if self.is_remote is True:
            return True

        # Probe the specified power controller
        if self.power is not None:
            status = self.power.probe()
            if status is False:
                print('Probe of the Power Controller failed!', file=sys.stderr)
                return False

        # Probe the specified storage controller
        if self.storage is not None:
            status = self.storage.probe()
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
                self, self.console, socket,
                self.power, b'CON', self._www)
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
                self, self.monitor, socket, self.power, b'MON')
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

        if self._www is not None:
            self._www.start()

        if self.is_server is True:
            handler = self._session_check
            self._session_timer = mtda.utils.RepeatTimer(10, handler)
            self._session_timer.start()

        # Start from a known state
        if self.power is not None:
            self._target_off()
            self.storage_to_target()
        else:
            # Assume the target is ON if we cannot control power delivery
            # and start logging on available console(s)
            if self.console_logger is not None:
                self.console_logger.resume()
            if self.monitor_logger is not None:
                self.monitor_logger.resume()

        return True

    def stop(self):
        self.mtda.debug(3, "main.stop()")

        if self.is_remote is True:
            return True

        # stop sesssion timer
        self._session_timer.cancel()

        # stop web service
        if self._www is not None:
            self._www.stop()

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
                self._sessions[session] = now + self._session_timeout

            # Check for inactive sessions
            inactive = []
            for s in self._sessions:
                left = self._sessions[s] - now
                self.mtda.debug(3, "session %s: %d seconds" % (s, left))
                if left <= 0:
                    inactive.append(s)
            for s in inactive:
                events.append("INACTIVE %s" % s)
                self._sessions.pop(s, "")

                # Check if we should arm the auto power-off timer
                # i.e. when the last session is removed and a power timeout
                # was set
                if len(self._sessions) == 0 and self._power_timeout > 0:
                    self._power_expiry = now + self._power_timeout
                    self.mtda.debug(2, "device will be powered down in {} "
                                       "seconds".format(self._power_timeout))

            if len(self._sessions) > 0:
                # There are active sessions: reset power expiry
                self._power_expiry = None
            else:
                # Otherwise check if we should auto-power off the target
                if self._power_expiry is not None and now > self._power_expiry:
                    self._lock_expiry = 0
                    power_off = True

            # Release device if the session owning the lock is idle
            if self._lock_owner is not None:
                if session == self._lock_owner:
                    self._lock_expiry = now + self._lock_timeout
                elif now >= self._lock_expiry:
                    events.append("UNLOCKED %s" % self._lock_owner)
                    self._lock_owner = None

        # Send event sessions generated above
        for e in events:
            self._session_event(e)

        # Check if we should auto power-off the device
        if power_off is True:
            self._target_off()
            self.mtda.debug(2, "device powered down after {} seconds of "
                               "inactivity".format(self._power_timeout))

        self.mtda.debug(3, "main._session_check: %s" % str(result))
        return result

    def _session_event(self, info):
        self.mtda.debug(3, "main._session_event(%s)" % str(info))

        result = None
        if info is not None:
            self.notify(CONSTS.EVENTS.SESSION, info)

        self.mtda.debug(3, "main._session_event: %s" % str(result))
        return result

    def _check_locked(self, session):
        self.mtda.debug(3, "main._check_locked()")

        owner = self.target_owner()
        if owner is None:
            return False
        status = False if session == owner else True
        return status

    @property
    def www(self):
        return self._www
