# ---------------------------------------------------------------------------
# MTDA main
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import configparser
import glob
import importlib
import os
import socket
import subprocess
import sys
import threading
import tempfile
import time

# Local imports
import mtda.constants as CONSTS
from mtda import __version__

# Pyro
try:
    from Pyro5.compatibility import Pyro4
except ImportError:
    import Pyro4


DEFAULT_PREFIX_KEY = 'ctrl-a'
DEFAULT_PASTEBIN_EP = "http://pastebin.com/api/api_post.php"

NBD_CONF_DIR = '/etc/nbd-server/conf.d'
NBD_CONF_FILE = 'mtda-storage.conf'


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
        self.keyboard = None
        self.mouse = None
        self.video = None
        self.mtda = self
        self.name = socket.gethostname()
        self.network = None
        self.assistant = None
        self.power = None
        self.power_on_script = None
        self.power_off_script = None
        self.power_monitors = []
        self.storage = None
        self._pastebin_api_key = None
        self._pastebin_endpoint = None
        self._session_manager = None
        self._session_timer = None
        self._storage_locked = False
        self._storage_mounted = False
        self._storage_opened = False
        self._storage_owner = None
        self._storage_status = CONSTS.STORAGE.UNKNOWN
        self._writer = None
        self._writer_data = None
        self.blksz = CONSTS.WRITER.READ_SIZE
        self.usb_switches = []
        self.ctrlport = 5556
        self.conport = 5557
        self.dataport = 0
        self.prefix_key = self._prefix_key_code(DEFAULT_PREFIX_KEY)
        self.is_remote = False
        self.is_server = False
        self.remote = None
        self._power_expiry = None
        self._power_lock = threading.Lock()
        self._socket_lock = threading.Lock()
        self._time_from_pwr = None
        self._time_from_str = None
        self._time_until_str = None
        self._uptime = 0
        self._www_host = None
        self._www_port = None
        self._www_workers = None
        self.version = __version__

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

    @Pyro4.expose
    def agent_version(self,  **kwargs):
        return self.version

    @Pyro4.expose
    def command(self, args, **kwargs):
        self.mtda.debug(3, "main.command()")

        result = False
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.power_locked(session) is False:
            result = self.power.command(args)

        self.mtda.debug(3, f"main.command(): {str(result)}")
        return result

    def _composite_needed(self):
        if self.console is not None and self.console.variant == 'usbf':
            return True
        if self.monitor is not None and self.monitor.variant == 'usbf':
            return True
        if self.storage is not None and self.storage.variant == 'usbf':
            return True
        if self.network is not None and self.network.variant == 'usbf':
            return True
        if self.keyboard is not None and self.keyboard.variant == 'hid':
            return True
        if self.mouse is not None and self.mouse.variant == 'hid':
            return True
        return False

    def _composite_start(self):
        self.mtda.debug(3, "main._composite_start()")

        result = True
        if self._composite_needed():
            from mtda.support.usb import Composite

            if self.storage is not None and self.storage.variant == 'usbf':
                status, _, _ = self.storage_status()
                enabled = status == CONSTS.STORAGE.ON_TARGET
                self.mtda.debug(3, "main._composite_start(): "
                                   f"with storage? {enabled}")
                Composite.storage_toggle(enabled)

            result = Composite.install()
            if result is True:
                if self.network is not None and self.network.variant == 'usbf':
                    self.network.up()

        self.mtda.debug(3, f"main._composite_start(): {result}")
        return result

    def _composite_stop(self):
        self.mtda.debug(3, "main._composite_stop()")

        result = None
        if self._composite_needed():
            from mtda.support.usb import Composite
            Composite.remove()

        self.mtda.debug(3, f"main._composite_stop(): {result}")
        return result

    @Pyro4.expose
    def config_set_power_timeout(self, timeout, **kwargs):
        self.mtda.debug(3, "main.config_set_power_timeout()")

        result = self._power_timeout
        self._power_timeout = timeout
        if timeout == 0:
            self._power_expiry = None
        session = kwargs.get("session", None)
        self.session_ping(session)

        self.mtda.debug(3, f"main.config_set_power_timeout(): {result}")
        return result

    @Pyro4.expose
    def config_set_session_timeout(self, timeout, **kwargs):
        self.mtda.debug(3, "main.config_set_session_timeout()")

        if timeout < CONSTS.SESSION.MIN_TIMEOUT:
            timeout = CONSTS.SESSION.MIN_TIMEOUT

        result = self._session_timeout
        self._session_timeout = timeout
        if self._session_manager is not None:
            self._session_manager.set_timeout(timeout)

        self.mtda.debug(3, f"main.config_set_session_timeout: {result}")
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
        self.mtda.debug(3, f"main.console_getkey(): {str(result)}")
        return result

    def console_init(self):
        from mtda.console.input import ConsoleInput
        self.console_input = ConsoleInput()
        self.console_input.start()

    @Pyro4.expose
    def console_clear(self, **kwargs):
        self.mtda.debug(3, "main.console_clear()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.console_locked(session):
            self.mtda.debug(2, "console_clear(): console is locked")
            return None
        if self.console_logger is not None:
            result = self.console_logger.clear()
        else:
            result = None

        self.mtda.debug(3, f"main.console_clear(): {str(result)}")
        return result

    @Pyro4.expose
    def console_dump(self, **kwargs):
        self.mtda.debug(3, "main.console_dump()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.console_locked(session):
            self.mtda.debug(2, "console_dump(): console is locked")
            return None

        result = None
        if self.console_logger is not None:
            result = self.console_logger.dump()

        self.mtda.debug(3, f"main.console_dump(): {str(result)}")
        return result

    @Pyro4.expose
    def console_flush(self, **kwargs):
        self.mtda.debug(3, "main.console_flush()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.console_locked(session):
            self.mtda.debug(2, "console_flush(): console is locked")
            return None

        result = None
        if self.console_logger is not None:
            result = self.console_logger.flush()

        self.mtda.debug(3, f"main.console_flush(): {str(result)}")
        return result

    @Pyro4.expose
    def console_head(self, **kwargs):
        self.mtda.debug(3, "main.console_head()")

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.console_logger is not None:
            result = self.console_logger.head()

        self.mtda.debug(3, f"main.console_head(): {str(result)}")
        return result

    @Pyro4.expose
    def console_lines(self, **kwargs):
        self.mtda.debug(3, "main.console_lines()")

        result = 0
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.console_logger is not None:
            result = self.console_logger.lines()

        self.mtda.debug(3, f"main.console_lines(): {str(result)}")
        return result

    def console_locked(self, session=None):
        self.mtda.debug(3, "main.console_locked()")

        result = self._check_locked(session)

        self.mtda.debug(3, f"main.console_locked(): {str(result)}")
        return result

    def console_port(self):
        return self.conport

    @Pyro4.expose
    def console_print(self, data, **kwargs):
        self.mtda.debug(3, "main.console_print()")

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.console_logger is not None:
            result = self.console_logger.print(data)

        self.mtda.debug(3, f"main.console_print(): {str(result)}")
        return result

    @Pyro4.expose
    def console_prompt(self, newPrompt=None, **kwargs):
        self.mtda.debug(3, "main.console_prompt()")

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.console_locked(session) is False and \
           self.console_logger is not None:
            result = self.console_logger.prompt(newPrompt)

        self.mtda.debug(3, f"main.console_prompt(): {str(result)}")
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
                from mtda.console.remote import RemoteConsole
                self.console_output = RemoteConsole(host, self.conport, screen)
                self.console_output.start()
            else:
                self.console_output = None

        self.mtda.debug(3, f"main.console_remote(): {str(result)}")
        return result

    @Pyro4.expose
    def console_run(self, cmd, **kwargs):
        self.mtda.debug(3, "main.console_run()")

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.console_locked(session) is False and \
           self.console_logger is not None:
            result = self.console_logger.run(cmd)

        self.mtda.debug(3, f"main.console_run(): {str(result)}")
        return result

    @Pyro4.expose
    def console_send(self, data, raw=False, **kwargs):
        self.mtda.debug(3, "main.console_send()")

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.console_locked(session) is False and \
           self.console_logger is not None:
            result = self.console_logger.write(data, raw)

        self.mtda.debug(3, f"main.console_send(): {str(result)}")
        return result

    @Pyro4.expose
    def console_tail(self, **kwargs):
        self.mtda.debug(3, "main.console_tail()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.console_locked(session) is False and \
           self.console_logger is not None:
            result = self.console_logger.tail()

        self.mtda.debug(3, f"main.console_tail(): {str(result)}")
        return result

    @Pyro4.expose
    def console_toggle(self, **kwargs):
        self.mtda.debug(3, "main.console_toggle()")

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.console_output is not None:
            self.console_output.toggle()
        if self.monitor_output is not None:
            self.monitor_output.toggle()

        self.mtda.debug(3, f"main.console_toggle(): {str(result)}")
        return result

    @Pyro4.expose
    def console_wait(self, what, timeout=None, **kwargs):
        self.mtda.debug(3, "main.console_wait()")

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        if session is not None and timeout is None:
            timeout = CONSTS.RPC.TIMEOUT
            self.warn('console_wait() without timeout, '
                      f'using default ({timeout})')
        if self.console_locked(session) is False and \
           self.console_logger is not None:
            result = self.console_logger.wait(what, timeout)

        self.mtda.debug(3, f"main.console_wait(): {str(result)}")
        return result

    def debug(self, level, msg):
        if self.debug_level >= level:
            if self.debug_level == 0:
                prefix = "# "
            else:
                prefix = "# debug%d: " % level
            msg = str(msg).replace("\n", f"\n{prefix} ... ")
            lines = msg.splitlines()
            sys.stderr.buffer.write(prefix.encode("utf-8"))
            for line in lines:
                sys.stderr.buffer.write(_make_printable(line).encode("utf-8"))
                sys.stderr.buffer.write(b"\n")
                sys.stderr.buffer.flush()

    def warn(self, msg):
        print(f'warning: {msg}', file=sys.stderr)

    def error(self, msg):
        print(f'error: {msg}', file=sys.stderr)

    @Pyro4.expose
    def env_get(self, name, default=None, **kwargs):
        self.mtda.debug(3, "env_get()")

        result = default
        if name in self.env:
            result = self.env[name]

        self.mtda.debug(3, f"env_get(): {str(result)}")
        return result

    @Pyro4.expose
    def env_set(self, name, value, **kwargs):
        self.mtda.debug(3, "env_set()")

        result = None

        if name in self.env:
            old_value = self.env[name]
            result = old_value
        else:
            old_value = value

        self.env[name] = value
        self.env[f"_{name}"] = old_value

        self.mtda.debug(3, f"env_set(): {str(result)}")
        return result

    def _keyboard_special_key(self, key):
        special_keys = {
                "<backspace>": self.keyboard.backspace,
                "<capslock>": self.keyboard.capsLock,
                "<enter>": self.keyboard.enter,
                "<tab>": self.keyboard.tab,

                "<esc>": self.keyboard.esc,
                "<f1>": self.keyboard.f1,
                "<f2>": self.keyboard.f2,
                "<f3>": self.keyboard.f3,
                "<f4>": self.keyboard.f4,
                "<f5>": self.keyboard.f5,
                "<f6>": self.keyboard.f6,
                "<f7>": self.keyboard.f7,
                "<f8>": self.keyboard.f8,
                "<f9>": self.keyboard.f9,
                "<f10>": self.keyboard.f10,
                "<f11>": self.keyboard.f11,
                "<f12>": self.keyboard.f12,

                "<left>": self.keyboard.left,
                "<right>": self.keyboard.right,
                "<up>": self.keyboard.up,
                "<down>": self.keyboard.down
                }
        if key in special_keys:
            return special_keys[key]
        return None

    @Pyro4.expose
    def keyboard_press(self, key, repeat=1, ctrl=False, shift=False,
                       alt=False, meta=False, **kwargs):
        self.mtda.debug(3, "main.keyboard_press()")

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.keyboard is not None:
            special_key = self._keyboard_special_key(key)
            if special_key is not None:
                result = special_key(repeat, ctrl, shift, alt, meta)
            else:
                result = self.keyboard.press(key, repeat, ctrl, shift,
                                             alt, meta)

        self.mtda.debug(3, f"main.keyboard_press(): {result}")
        return result

    @Pyro4.expose
    def keyboard_write(self, what, **kwargs):
        self.mtda.debug(3, "main.keyboard_write()")

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.keyboard is not None:
            while what != "":
                # check for special keys such as <esc>
                if what.startswith('<') and '>' in what:
                    key = what.split('>')[0] + '>'
                    special_key = self._keyboard_special_key(key)
                    if special_key is not None:
                        offset = len(key)
                        what = what[offset:]
                        special_key()
                        continue
                key = what[0]
                what = what[1:]
                self.keyboard.write(key)

        self.mtda.debug(3, f"main.keyboard_write(): {result}")
        return result

    @Pyro4.expose
    def mouse_move(self, x, y, buttons, **kwargs):
        self.mtda.debug(3, "main.mouse_move()")

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.mouse is not None:
            self.mouse.move(x, y, buttons)

        self.mtda.debug(3, f"main.mouse_move(): {result}")
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
                from mtda.console.remote import RemoteMonitor
                self.monitor_output = RemoteMonitor(host, self.conport, screen)
                self.monitor_output.pause()
                self.monitor_output.start()
            else:
                self.monitor_output = None

        self.mtda.debug(3, f"main.monitor_remote(): {str(result)}")
        return result

    @Pyro4.expose
    def monitor_send(self, data, raw=False, **kwargs):
        self.mtda.debug(3, "main.monitor_send()")

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.console_locked(session) is False and \
           self.monitor_logger is not None:
            result = self.monitor_logger.write(data, raw)

        self.mtda.debug(3, f"main.monitor_send(): {str(result)}")
        return result

    @Pyro4.expose
    def monitor_wait(self, what, timeout=None, **kwargs):
        self.mtda.debug(3, "main.monitor_wait()")

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        if session is not None and timeout is None:
            timeout = CONSTS.RPC.TIMEOUT
            self.warn('monitor_wait() called without timeout, '
                      'using default({})'.format(timeout))
        if self.console_locked(session) is False and \
           self.monitor_logger is not None:
            result = self.monitor_logger.wait(what, timeout)

        self.mtda.debug(3, f"main.monitor_wait(): {str(result)}")
        return result

    def pastebin_api_key(self):
        self.mtda.debug(3, "main.pastebin_api_key()")
        return self._pastebin_api_key

    def pastebin_endpoint(self):
        self.mtda.debug(3, "main.pastebin_endpoint()")
        return self._pastebin_endpoint

    def power_locked(self, session=None):
        self.mtda.debug(3, "main.power_locked()")

        self.session_ping(session)
        if self.power is None:
            result = True
        else:
            result = self._check_locked(session)

        self.mtda.debug(3, f"main.power_locked(): {str(result)}")
        return result

    def publish(self, topic, data):
        if self.socket is not None:
            import zmq
            with self._socket_lock:
                self.socket.send(topic, flags=zmq.SNDMORE)
                self.socket.send(data)

    def _storage_event(self, status, reason=""):
        if status in [CONSTS.STORAGE.ON_HOST,
                      CONSTS.STORAGE.ON_NETWORK,
                      CONSTS.STORAGE.ON_TARGET]:
            self._storage_status = status
        if reason:
            status = status + " " + reason
        self.notify(CONSTS.EVENTS.STORAGE, status)

    @Pyro4.expose
    def storage_compression(self, compression, **kwargs):
        self.mtda.debug(3, "main.storage_compression()")

        if self.storage is None:
            result = None
        else:
            result = self._writer.compression.value
            self._writer.compression = compression

        self.mtda.debug(3, f"main.storage_compression(): {result}")
        return result

    @Pyro4.expose
    def storage_bmap_dict(self, bmapDict, **kwargs):
        self.mtda.debug(3, "main.storage_bmap_dict()")

        result = None
        if self.storage is not None:
            self.storage.setBmap(bmapDict)
            result = True
        self.mtda.debug(3, f"main.storage_bmap_dict()(): {result}")

    @Pyro4.expose
    def storage_close(self, **kwargs):
        self.mtda.debug(3, "main.storage_close()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.storage is None:
            result = False
        else:
            conf = os.path.join(NBD_CONF_DIR, NBD_CONF_FILE)
            if os.path.exists(conf):
                os.unlink(conf)
                cmd = ['systemctl', 'restart', 'nbd-server']
                subprocess.check_call(cmd)

            self._writer.stop()
            self._writer_data = None
            self._storage_opened = not self.storage.close()
            self._storage_owner = None
            result = (self._storage_opened is False)

        if self.storage is not None:
            self.storage_locked()

        self.mtda.debug(3, f"main.storage_close(): {result}")
        return result

    @Pyro4.expose
    def storage_commit(self, **kwargs):
        self.mtda.debug(3, "main.storage_commit()")

        session = kwargs.get("session", None)
        self.session_ping(session)

        result = False
        if self.storage is not None:
            if self.storage_locked(session):
                raise RuntimeError('cannot commit changes, '
                                   'storage is locked!')
            result = self.storage.commit()

        self.mtda.debug(3, f"main.storage_commit(): {result}")
        return result

    @Pyro4.expose
    def storage_rollback(self, **kwargs):
        self.mtda.debug(3, "main.storage_rollback()")

        session = kwargs.get("session", None)
        self.session_ping(session)

        result = False
        if self.storage is not None:
            if self.storage_locked(session):
                raise RuntimeError('cannot rollback changes, '
                                   'storage is locked!')
            result = self.storage.rollback()

        self.mtda.debug(3, f"main.storage_rollback(): {result}")
        return result

    @Pyro4.expose
    def storage_flush(self, size, **kwargs):
        self.mtda.debug(3, f"main.storage_flush({size})")

        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.storage is None:
            result = False
        else:
            result = self._writer.flush(size)

        self.mtda.debug(3, f"main.storage_flush(): {result}")
        return result

    def storage_locked(self, session=None):
        self.mtda.debug(3, "main.storage_locked()")

        result = False
        reason = "unsure"
        self.session_ping(session)
        if self._check_locked(session):
            reason = "target is locked"
            result = True
        # Cannot swap the shared storage device between the host and target
        # without a driver
        elif self.storage is None:
            reason = "no shared storage device"
            result = True
        # If hotplugging is supported, swap only if the shared storage
        # isn't opened
        elif self.storage.supports_hotplug() is True:
            result = self._storage_opened
            if result is True:
                reason = "hotplug supported but storage is opened"
        # We also need a power controller to be safe
        elif self.power is None:
            reason = "no power controller"
            result = True
        # The target shall be OFF
        elif self._target_status() != "OFF":
            reason = "target is on"
            result = True
        elif (self._storage_status == CONSTS.STORAGE.ON_NETWORK and
              self._storage_owner is not None and
              self._storage_owner != session):
            reason = ("storage shared on the network for " +
                      f"{self._storage_owner}")
            result = True
        # Lastly, the shared storage device shall not be opened
        elif self._storage_opened is True:
            reason = "shared storage is in use (opened)"
            result = True

        if result is True:
            self.mtda.debug(4, f"storage_locked(): {reason}")
            event = CONSTS.STORAGE.LOCKED
        else:
            event = CONSTS.STORAGE.UNLOCKED
            reason, _, _ = self.storage_status()

        # Notify UI if storage becomes locked/unlocked
        if result != self._storage_locked:
            self._storage_locked = result
            self._storage_event(event, reason)

        self.mtda.debug(3, f"main.storage_locked(): {result}")
        return result

    @Pyro4.expose
    def storage_mount(self, part=None, **kwargs):
        self.mtda.debug(3, "main.storage_mount()")

        session = kwargs.get("session", None)
        self.session_ping(session)

        if self.storage is None:
            raise RuntimeError('no shared storage device')
        elif self.storage.is_storage_mounted is True:
            raise RuntimeError("already mounted")
        elif self.storage_locked(session) is True:
            raise RuntimeError('shared storage in use')
        elif self.storage.to_host() is True:
            result = self.storage.mount(part)
            self._storage_mounted = (result is True)
            self._storage_owner = session
            self.storage_locked()

        self.mtda.debug(3, f"main.storage_mount(): {result}")
        return result

    @Pyro4.expose
    def storage_update(self, dst, size, stream=None, **kwargs):
        self.mtda.debug(3, "main.storage_update()")

        result = False
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.storage is None:
            raise RuntimeError('no shared storage device')
        elif self.storage_locked(session) is True:
            raise RuntimeError('shared storage in use')
        elif self.storage.is_storage_mounted is False:
            raise RuntimeError("not mounted")
        else:
            try:
                self.storage.update(dst)
                result = self._storage_socket(session, size, stream)
            except (FileNotFoundError, IOError) as e:
                self.mtda.debug(1, f"main.storage_update(): {str(e.args[0])}")

        self.mtda.debug(3, f"main.storage_update(): {result}")
        return result

    @Pyro4.expose
    def storage_network(self, **kwargs):
        self.mtda.debug(3, "main.storage_network()")

        result = False
        session = kwargs.get("session", None)
        self.session_ping(session)

        if self.storage is None:
            raise RuntimeError('no shared storage device')
        elif hasattr(self.storage, 'path') is False:
            raise RuntimeError('path to shared storage not available')
        elif os.path.exists(NBD_CONF_DIR) is False:
            raise RuntimeError('NBD configuration directory not found')
        elif self.storage_locked(session) is True:
            raise RuntimeError('shared storage in use')
        elif self.storage.to_host() is True:
            file = self.storage.path()
            if file:
                conf = os.path.join(NBD_CONF_DIR, NBD_CONF_FILE)
                with open(conf, 'w') as f:
                    f.write('[mtda-storage]\n')
                    f.write('authfile = /etc/nbd-server/allow\n')
                    f.write(f'exportname = {file}\n')
                    f.close()

                cmd = ['systemctl', 'restart', 'nbd-server']
                subprocess.check_call(cmd)

                cmd = ['systemctl', 'is-active', 'nbd-server']
                subprocess.check_call(cmd)

                self._storage_owner = session
                self.storage_locked()
                self._storage_event(CONSTS.STORAGE.ON_NETWORK)
                result = True
            else:
                raise RuntimeError('no path to shared storage')

        self.mtda.debug(3, f"main.storage_network(): {result}")
        return result

    @Pyro4.expose
    def storage_open(self, size=0, stream=None, **kwargs):
        self.mtda.debug(3, 'main.storage_open()')

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        owner = self._storage_owner
        status, _, _ = self.storage_status()

        if self.storage is None:
            raise RuntimeError('no shared storage device')
        elif status != CONSTS.STORAGE.ON_HOST:
            raise RuntimeError('shared storage not attached to host')
        elif owner is not None and owner != session:
            raise RuntimeError('shared storage in use')
        elif self._storage_opened is False:
            try:
                self.storage.open()
                self._storage_opened = True
                self._storage_owner = session
                self.storage_locked()
                self._storage_event(CONSTS.STORAGE.OPENED, session)
            except Exception:
                raise RuntimeError('shared storage could not be opened!')
            result = self._storage_socket(session, size, stream)

        self.mtda.debug(3, f'main.storage_open(): {result}')
        return result

    def _storage_socket(self, session, size, stream=None):
        if stream is None:
            from mtda.storage.datastream import NetworkDataStream
            stream = NetworkDataStream(self.dataport)
        return self._writer.start(session, size, stream)

    @Pyro4.expose
    def storage_status(self, **kwargs):
        self.mtda.debug(3, "main.storage_status()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.storage is None:
            self.mtda.debug(4, "storage_status(): no shared storage device")
            result = CONSTS.STORAGE.UNKNOWN, False, 0
        else:
            result = (self._storage_status,
                      self._writer.writing,
                      self._writer.written)

        self.mtda.debug(3, f"main.storage_status(): {str(result)}")
        return result

    @Pyro4.expose
    def storage_toggle(self, **kwargs):
        self.mtda.debug(3, "main.storage_status()")

        result = CONSTS.STORAGE.UNKNOWN
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.storage is None:
            self.mtda.debug(4, "storage_toggle(): no shared storage device")
        else:
            status, _, _ = self.storage_status()
            if status in (CONSTS.STORAGE.ON_HOST, CONSTS.STORAGE.ON_NETWORK):
                if self.storage_to_target(session=session):
                    result = CONSTS.STORAGE.ON_TARGET
            elif status == CONSTS.STORAGE.ON_TARGET:
                if self.storage_to_host(session=session):
                    result = CONSTS.STORAGE.ON_HOST

        self.mtda.debug(3, f"main.storage_toggle(): {result}")
        return result

    @Pyro4.expose
    def storage_to_host(self, **kwargs):
        self.mtda.debug(3, "main.storage_to_host()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.storage_locked(session) is False:
            result = self.storage.to_host()
            if result is True:
                self._storage_event(CONSTS.STORAGE.ON_HOST)
        else:
            self.error('cannot switch storage to host: locked')
            result = False

        self.mtda.debug(3, f"main.storage_to_host(): {result}")
        return result

    @Pyro4.expose
    def storage_to_target(self, **kwargs):
        self.mtda.debug(3, "main.storage_to_target()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.storage_locked(session) is False:
            self.storage_close()
            result = self.storage.to_target()
            if result is True:
                self._storage_event(CONSTS.STORAGE.ON_TARGET)
        else:
            self.error('cannot switch storage to target: locked')
            result = False

        self.mtda.debug(3, f"main.storage_to_target(): {str(result)}")
        return result

    @Pyro4.expose
    def storage_swap(self, **kwargs):
        self.mtda.debug(3, "main.storage_swap()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.storage_locked(session) is False:
            result, writing, written = self.storage_status(session=session)
            if result in [CONSTS.STORAGE.ON_HOST, CONSTS.STORAGE.ON_NETWORK]:
                if self.storage.to_target() is True:
                    self._storage_event(CONSTS.STORAGE.ON_TARGET)
            elif result == CONSTS.STORAGE.ON_TARGET:
                if self.storage.to_host() is True:
                    self._storage_event(CONSTS.STORAGE.ON_HOST)
        result, writing, written = self.storage_status(session=session)
        return result

        self.mtda.debug(3, f"main.storage_swap(): {str(result)}")
        return result

    def storage_write(self, data, **kwargs):
        self.mtda.debug(3, "main.storage_write()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        result = self._writer.enqueue(data, callback=self._storage_event)

        self.mtda.debug(3, f"main.storage_write(): {result}")
        return result

    def systemd_configure(self):
        from filecmp import dircmp

        console = self.console
        storage = self.storage
        video = self.video

        self.systemd_configure_www()
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
            import shutil
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

    def systemd_configure_www(self):
        self.mtda.debug(3, "main.systemd_configure_www()")

        result = None
        etcdir = '/etc/systemd/system/mtda-www.service.d/'
        if self._www_port or self._www_host or self._www_workers:
            os.makedirs(etcdir, exist_ok=True)
            dropin = os.path.join(etcdir, 'www.conf')
            with open(dropin, 'w') as f:
                f.write('[Service]\n')
                if self.debug_level:
                    f.write('Environment=DEBUG_ARG=--debug\n')
                if self._www_host:
                    f.write(f'Environment=HOST={self._www_host}\n')
                if self._www_port:
                    f.write(f'Environment=PORT={self._www_port}\n')
                if self._www_workers:
                    f.write(f'Environment=WORKERS={self._www_workers}\n')
        else:
            import shutil
            shutil.rmtree(etcdir, ignore_errors=True)

        self.mtda.debug(3, f"main.systemd_configure_www(): {result}")
        return result

    @Pyro4.expose
    def toggle_timestamps(self, **kwargs):
        # kwargs: might be called with session parameter
        self.mtda.debug(3, "main.toggle_timestamps()")

        if self.console_logger is not None:
            result = self.console_logger.toggle_timestamps()
        else:
            print("no console configured/found!", file=sys.stderr)
            result = None

        self.mtda.debug(3, f"main.toggle_timestamps(): {str(result)}")
        return result

    @Pyro4.expose
    def target_lock(self, **kwargs):
        self.mtda.debug(3, "main.target_lock()")

        result = False
        session = kwargs.get("session", None)
        if self._session_manager is not None:
            result = self._session_manager.lock(session)

        self.mtda.debug(3, f"main.target_lock: {result}")
        return result

    @Pyro4.expose
    def target_locked(self, **kwargs):
        self.mtda.debug(3, "main.target_locked()")

        result = False
        session = kwargs.get("session", None)
        if self._session_manager:
            result = self._session_manager.locked(session) is not None

        self.mtda.debug(3, f"main.target_locked: {result}")
        return result

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
        import gevent
        import mtda.scripts

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
        import mtda.scripts

        env = self._env_for_script()
        mtda.scripts.load_device_scripts(env['variant'], env)
        for e in env.keys():
            setattr(mtda.scripts, e, env[e])

    def _parse_script(self, script):
        self.mtda.debug(3, "main._parse_script()")

        result = None
        if script is not None:
            result = script.replace("... ", "    ")

        self.mtda.debug(3, f"main._parse_script(): {str(result)}")
        return result

    def exec_power_on_script(self):
        self.mtda.debug(3, "main.exec_power_on_script()")

        result = None
        if self.power_on_script:
            self.mtda.debug(4, "exec_power_on_script(): "
                               f"{self.power_on_script}")
            env = self._env_for_script()
            result = exec(self.power_on_script, env)

        self.mtda.debug(3, f"main.exec_power_on_script(): {str(result)}")
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

        if self.storage is not None:
            self.storage_locked()

        self.mtda.debug(3, f"main._target_on(): {result}")
        return result

    @Pyro4.expose
    def target_on(self, **kwargs):
        self.mtda.debug(3, "main.target_on()")

        result = True
        session = kwargs.get("session", None)
        self.session_ping(session)
        with self._power_lock:
            status = self._target_status()
            if status != CONSTS.POWER.ON:
                result = False
                if self.power_locked(session) is False:
                    result = self._target_on(session)

        self.mtda.debug(3, f"main.target_on(): {result}")
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

        # bring network down
        if self.network is not None:
            self.network.down()

        # release keyboard
        if self.keyboard is not None:
            self.keyboard.idle()

        # release mouse
        if self.mouse is not None:
            self.mouse.idle()

        result = True
        if self.power is not None:
            result = self.power.off()
        self._composite_stop()
        self._power_event(CONSTS.POWER.OFF)

        if self.storage is not None:
            self.storage_locked()

        self.mtda.debug(3, f"main._target_off(): {result}")
        return result

    @Pyro4.expose
    def target_off(self, **kwargs):
        self.mtda.debug(3, "main.target_off()")

        result = True
        session = kwargs.get("session", None)
        self.session_ping(session)
        with self._power_lock:
            status = self._target_status()
            if status != CONSTS.POWER.OFF:
                result = False
                if self.power_locked(session) is False:
                    result = self._target_off(session)

        self.mtda.debug(3, f"main.target_off(): {result}")
        return result

    def _target_status(self, session=None):
        self.mtda.debug(3, "main._target_status()")

        if self.power is None:
            result = CONSTS.POWER.UNSURE
        else:
            result = self.power.status()

        self.mtda.debug(3, f"main._target_status(): {result}")
        return result

    @Pyro4.expose
    def target_status(self, **kwargs):
        self.mtda.debug(3, "main.target_status()")

        session = kwargs.get("session", None)
        with self._power_lock:
            result = self._target_status(session)

        self.mtda.debug(3, f"main.target_status(): {result}")
        return result

    @Pyro4.expose
    def target_toggle(self, **kwargs):
        self.mtda.debug(3, "main.target_toggle()")

        result = CONSTS.POWER.UNSURE
        session = kwargs.get("session", None)
        self.session_ping(session)
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

        self.mtda.debug(3, f"main.target_toggle(): {result}")
        return result

    @Pyro4.expose
    def target_unlock(self, **kwargs):
        self.mtda.debug(3, "main.target_unlock()")

        result = False
        session = kwargs.get("session", None)
        if self._session_manager is not None:
            result = self._session_manager.unlock(session)

        self.mtda.debug(3, f"main.target_unlock: {result}")
        return result

    @Pyro4.expose
    def target_uptime(self, **kwargs):
        self.mtda.debug(3, "main.target_uptime()")

        result = 0
        if self._uptime > 0:
            result = time.monotonic() - self._uptime

        self.mtda.debug(3, f"main.target_uptime(): {str(result)}")
        return result

    @Pyro4.expose
    def usb_find_by_class(self, className, **kwargs):
        self.mtda.debug(3, "main.usb_find_by_class()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        ports = len(self.usb_switches)
        ndx = 0
        while ndx < ports:
            usb_switch = self.usb_switches[ndx]
            if usb_switch.className == className:
                return usb_switch
            ndx = ndx + 1
        return None

    @Pyro4.expose
    def usb_has_class(self, className, **kwargs):
        self.mtda.debug(3, "main.usb_has_class()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        usb_switch = self.usb_find_by_class(className, session)
        return usb_switch is not None

    @Pyro4.expose
    def usb_off(self, ndx, **kwargs):
        self.mtda.debug(3, "main.usb_off()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                usb_switch.off()
        except IndexError:
            print("invalid USB switch #" + str(ndx), file=sys.stderr)

    @Pyro4.expose
    def usb_off_by_class(self, className, **kwargs):
        self.mtda.debug(3, "main.usb_off_by_class()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        usb_switch = self.usb_find_by_class(className, session)
        if usb_switch is not None:
            return usb_switch.off()
        return False

    @Pyro4.expose
    def usb_on(self, ndx, **kwargs):
        self.mtda.debug(3, "main.usb_on()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                usb_switch.on()
        except IndexError:
            print("invalid USB switch #" + str(ndx), file=sys.stderr)

    @Pyro4.expose
    def usb_on_by_class(self, className, **kwargs):
        self.mtda.debug(3, "main.usb_on_by_class()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        usb_switch = self.usb_find_by_class(className, session)
        if usb_switch is not None:
            return usb_switch.on()
        return False

    @Pyro4.expose
    def usb_ports(self, **kwargs):
        self.mtda.debug(3, "main.usb_ports()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        return len(self.usb_switches)

    @Pyro4.expose
    def usb_status(self, ndx, **kwargs):
        self.mtda.debug(3, "main.usb_status()")

        session = kwargs.get("session", None)
        self.session_ping(session)
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

    @Pyro4.expose
    def usb_toggle(self, ndx, **kwargs):
        self.mtda.debug(3, "main.usb_toggle()")

        session = kwargs.get("session", None)
        self.session_ping(session)
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                usb_switch.toggle()
        except IndexError:
            print("invalid USB switch #" + str(ndx), file=sys.stderr)

    @Pyro4.expose
    def video_format(self, **kwargs):
        self.mtda.debug(3, "main.video_format()")

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.video is not None:
            result = self.video.format

        self.mtda.debug(3, f"main.video_format(): {result}")
        return result

    @Pyro4.expose
    def video_url(self, host="", opts=None, **kwargs):
        self.mtda.debug(3, f"main.video_url(host={host}, opts={opts})")

        result = None
        session = kwargs.get("session", None)
        self.session_ping(session)
        if self.video is not None:
            result = self.video.url(host, opts)

        self.mtda.debug(3, f"main.video_url(): {result}")
        return result

    def load_config(self, remote=None, is_server=False, config_files=None):
        self.mtda.debug(3, "main.load_config()")

        if config_files is None:
            config_files = os.getenv('MTDA_CONFIG', self.config_files)

        self.mtda.debug(2, f"main.load_config(): config_files={config_files}")

        self.remote = os.getenv('MTDA_REMOTE', remote)
        self.is_remote = self.remote is not None
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
            subsystems = ['power', 'console', 'storage', 'monitor', 'network',
                          'keyboard', 'mouse', 'video', 'assistant']
            for sub in subsystems:
                if parser.has_section(sub):
                    try:
                        postconf = None
                        hook = f'post_configure_{sub}'
                        if hasattr(self, hook):
                            postconf = getattr(self, hook)
                        self.load_subsystem(sub, parser, postconf)
                    except RuntimeError:
                        self.error(f"configuration of {sub} failed!")
                    except configparser.NoOptionError:
                        self.error(f"variant not defined for '{sub}'!")
                    except ImportError:
                        self.error(f"{sub} could not be found/loaded!")
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

            # web-based UI
            if parser.has_section('www'):
                self.load_www_config(parser)

    def load_main_config(self, parser):
        self.mtda.debug(3, "main.load_main_config()")

        # Name of this agent
        self.name = parser.get('main', 'name', fallback=self.name)

        self.mtda.debug_level = int(
            parser.get('main', 'debug', fallback=self.mtda.debug_level))

    def load_environment(self, parser):
        self.mtda.debug(3, "main.load_environment()")

        for opt in parser.options('environment'):
            value = parser.get('environment', opt)
            self.mtda.debug(4, f"main.load_environment(): {opt} => {value}")
            self.env_set(opt, value)

    def load_subsystem(self, subsystem, parser, postconf=None):
        variant = parser.get(subsystem, 'variant')
        mod = importlib.import_module(f"mtda.{subsystem}.{variant}")
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

        from mtda.storage.writer import AsyncImageWriter
        self._writer = AsyncImageWriter(self, storage)

        import atexit
        atexit.register(self.storage_close)

    def load_remote_config(self, parser):
        self.mtda.debug(3, "main.load_remote_config()")

        self.conport = int(
            parser.get('remote', 'console', fallback=self.conport))
        self.ctrlport = int(
            parser.get('remote', 'control', fallback=self.ctrlport))
        self.dataport = int(
            parser.get('remote', 'data', fallback=self.dataport))
        if self.is_server is False:
            if self.remote is None:
                # Load remote setting from the configuration
                self.remote = parser.get(
                    'remote', 'host', fallback=self.remote)

            # Attempt to resolve remote using Zeroconf
            import mtda.discovery
            watcher = mtda.discovery.Watcher(CONSTS.MDNS.TYPE)
            ip = watcher.lookup(self.remote)
            if ip is not None:
                self.debug(2, f"resolved '{self.remote}' "
                              f"({ip}) using Zeroconf")
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

        self.mtda.debug(3, f"main.load_timeouts_config: {str(result)}")
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
            print(f'usb switch "{variant}" could not be found/loaded!',
                  file=sys.stderr)

    def load_www_config(self, parser):
        self.mtda.debug(3, "main.load_www_config()")
        self._www_host = parser.get('www', 'host',
                                    fallback=CONSTS.DEFAULTS.WWW_HOST)
        self._www_port = int(
                parser.get('www', 'port',
                           fallback=CONSTS.DEFAULTS.WWW_PORT))
        self._www_workers = int(
                parser.get('www', 'workers',
                           fallback=CONSTS.DEFAULTS.WWW_WORKERS))

    def notify(self, what, info):
        self.mtda.debug(4, f"main.notify({what},{info})")

        result = None
        if self.socket is not None:
            import zmq
            with self._socket_lock:
                self.socket.send(CONSTS.CHANNEL.EVENTS, flags=zmq.SNDMORE)
                self.socket.send_string(f"{what} {info}")

        self.mtda.debug(4, f"main.notify: {result}")
        return result

    def notify_write(self, size=0):
        if self._writer:
            self._writer.notify_write(size=size)

    def start(self):
        self.mtda.debug(3, "main.start()")

        if self.is_remote is True:
            return True

        # Create session manager to support multiple users
        from mtda.session import SessionManager
        self._session_manager = SessionManager(self,
                                               self._lock_timeout,
                                               self._session_timeout)

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
            self._storage_event(CONSTS.STORAGE.UNLOCKED)

        if self.console is not None or self.monitor is not None:
            # Create a publisher
            if self.is_server is True:
                from mtda.console.logger import ConsoleLogger
                import zmq
                context = zmq.Context()
                socket = context.socket(zmq.PUB)
                socket.bind(f"tcp://*:{self.conport}")
            else:
                socket = None
            self.socket = socket

        if self.console is not None:
            # Create and start console logger
            status = self.console.probe()
            if status is False:
                print('Probe of the %s console failed!' % (
                      self.console.variant), file=sys.stderr)
                return False
            self.console_logger = ConsoleLogger(
                self, self.console, socket, self.power, b'CON')
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

        if self.network is not None:
            status = self.network.probe()
            if status is False:
                print('Probe of the %s network failed!' % (
                      self.network.variant), file=sys.stderr)
                return False

        if self.keyboard is not None:
            status = self.keyboard.probe()
            if status is False:
                print('Probe of the %s keyboard failed!' % (
                      self.keyboard.variant), file=sys.stderr)
                return False

        if self.mouse is not None:
            status = self.mouse.probe()
            if status is False:
                print('Probe of the %s mouse failed!' % (
                      self.mouse.variant), file=sys.stderr)
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
            from mtda.utils import RepeatTimer
            self._session_timer = RepeatTimer(5, self._timer)
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
        if self._session_timer:
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

    def session_check(self):
        self.mtda.debug(4, "main.session_check()")

        self._session_manager.check()

        now = time.monotonic()
        if self._power_expiry is not None and now > self._power_expiry:
            self._target_off()
            self._power_expiry = None
            self.mtda.debug(2, "device powered down after "
                               f"{self._power_timeout} seconds of inactivity")

        self.mtda.debug(4, "main.session_check: exit")

    def session_event(self, info):
        self.mtda.debug(4, f"main.session_event({info})")

        info = info.split()
        event = info[0]
        now = time.monotonic()

        if event == CONSTS.SESSION.NONE:
            # Check if we should arm the auto power-off timer
            # i.e. when the last session is removed and a power timeout
            # was set
            if self._power_timeout > 0:
                self._power_expiry = now + self._power_timeout
                self.mtda.debug(2, "device will be powered down in "
                                   f"{self._power_timeout} seconds")

        elif event == CONSTS.SESSION.RUNNING:
            # There are active sessions: reset power expiry
            self._power_expiry = None

        elif event == CONSTS.SESSION.INACTIVE:
            # If a session had the shared storage device opened but has gone
            # quiet, close it to let others grab it. Let's assume that its
            # content is corrupted: send a storage event that UIs may use to
            # display a warning
            session = info[1]
            if self._storage_opened is True and self._storage_owner == session:
                self.mtda.debug(2, "closing storage for idle session "
                                   f"{session}, storage may be corrupted!")
                self._storage_event(CONSTS.STORAGE.CORRUPTED)
                self.storage_close(session=session)

    def session_ping(self, session=None):
        self.mtda.debug(4, f"main.session_ping({session})")

        result = None
        if self._session_manager is not None:
            result = self._session_manager.ping(session)

        self.mtda.debug(4, f"main.session_ping: {result}")
        return result

    def _check_locked(self, session):
        self.mtda.debug(3, "main._check_locked()")

        owner = None
        if self._session_manager is not None:
            owner = self._session_manager.locked(session)
        result = (owner is not None and session == owner)

        self.mtda.debug(3, f"main._check_locked: {result}")
        return result

    def _system_monitor(self):
        loadavg = 0.0
        with open('/proc/loadavg') as f:
            stats = f.readline().split()
            loadavg = stats[0]
        self.notify(CONSTS.EVENTS.SYSTEM, f'{loadavg}')

    def _timer(self):
        # Check for inative sessions
        self.session_check()

        # System health checks
        self._system_monitor()
