# System imports
import bz2
import configparser
import daemon
import gevent
import importlib
import os
import signal
import sys
import time
import zlib
import zmq

# Local imports
from   mtda.console.input import ConsoleInput
from   mtda.console.logger import ConsoleLogger
from   mtda.console.remote_output import RemoteConsoleOutput
import mtda.keyboard.controller
import mtda.power.controller

_NOPRINT_TRANS_TABLE = {
    i: '.' for i in range(0, sys.maxunicode + 1) if not chr(i).isprintable()
}

def _make_printable(s):
    return s.translate(_NOPRINT_TRANS_TABLE)

class MentorTestDeviceAgent:

    def __init__(self):
        self.config_files = [ 'mtda.ini' ]
        self.console = None
        self.console_logger = None
        self.console_input = None
        self.console_output = None
        self.debug_level = 0
        self.env = {}
        self.keyboard = None
        self.mtda = self
        self.power_controller = None
        self.power_on_script = None
        self.power_off_script = None
        self.sdmux_controller = None
        self._storage_bytes_written = 0
        self._storage_mounted = False
        self._storage_opened = False
        self.blksz = 1 * 1024 * 1024
        self.bz2dec = None
        self.zdec = None
        self.fbintvl = 8 # Feedback interval
        self.usb_switches = []
        self.ctrlport = 5556
        self.conport = 5557
        self.is_remote = False
        self.is_server = False
        self.remote = None
        self._lock_owner = None
        self._lock_expiry = None
        self._lock_timeout = 5 # Lock timeout (in minutes)

        # Config file in $HOME/.mtda/config
        home = os.getenv('HOME', '')
        if home != '':
            self.config_files.append(os.path.join(home, '.mtda', 'config'))

        # Config file in /etc/mtda/config
        if os.path.exists('/etc'):
            self.config_files.append(os.path.join('/etc', 'mtda', 'config'))

    def console_getkey(self):
        self.mtda.debug(3, "main.console_getkey()")

        if self.console_input is None:
            self.console_input = ConsoleInput()
            self.console_input.start()
        result = self.console_input.getkey()

        self.mtda.debug(3, "main.console_getkey(): %s" % str(result))
        return result

    def console_clear(self, session=None):
        self.mtda.debug(3, "main.console_clear()")

        self._check_expired(session)
        if self.console_locked(session):
            self.mtda.debug(2, "console_clear(): console is locked")
            return None
        if self.console_logger is not None:
            result = self.console_logger.clear()
        else:
            result = None

        self.mtda.debug(3, "main.console_clear(): %s" % str(result))
        return result

    def console_flush(self, session=None):
        self.mtda.debug(3, "main.console_flush()")

        self._check_expired(session)
        if self.console_locked(session):
            self.mtda.debug(2, "console_clear(): console is locked")
            return None

        result = None
        if self.console_logger is not None:
            result = self.console_logger.flush()

        self.mtda.debug(3, "main.console_flush(): %s" % str(result))
        return result

    def console_head(self, session=None):
        self.mtda.debug(3, "main.console_head()")

        self._check_expired(session)
        result = None
        if self.console_logger is not None:
            result = self.console_logger.head()

        self.mtda.debug(3, "main.console_head(): %s" % str(result))
        return result

    def console_lines(self, session=None):
        self.mtda.debug(3, "main.console_lines()")

        self._check_expired(session)
        result = None
        if self.console_logger is not None:
            result = self.console_logger.lines()

        self.mtda.debug(3, "main.console_lines(): %s" % str(result))
        return result

    def console_locked(self, session=None):
        self.mtda.debug(3, "main.console_locked()")

        self._check_expired(session)
        result = self._check_locked(session)

        self.mtda.debug(3, "main.console_locked(): %s" % str(result))
        return result

    def console_print(self, data, session=None):
        self.mtda.debug(3, "main.console_print()")

        self._check_expired(session)
        result = None
        if self.console_logger is not None:
            result = self.console_logger.print(data)

        self.mtda.debug(3, "main.console_print(): %s" % str(result))
        return result

    def console_prompt(self, newPrompt=None, session=None):
        self.mtda.debug(3, "main.console_prompt()")

        self._check_expired(session)
        result = None
        if self.console_locked(session) == False and self.console_logger is not None:
            result = self.console_logger.prompt(newPrompt)

        self.mtda.debug(3, "main.console_prompt(): %s" % str(result))
        return result

    def console_remote(self, host):
        self.mtda.debug(3, "main.console_remote()")

        result = None
        if self.is_remote == True:
            # Create and start our remote console
            self.console_output = RemoteConsoleOutput(host, self.conport)
            self.console_output.start()

        self.mtda.debug(3, "main.console_remote(): %s" % str(result))
        return result

    def console_run(self, cmd, session=None):
        self.mtda.debug(3, "main.console_run()")

        self._check_expired(session)
        result = None
        if self.console_locked(session) == False and self.console_logger is not None:
            result = self.console_logger.run(cmd)

        self.mtda.debug(3, "main.console_run(): %s" % str(result))
        return result

    def console_send(self, data, raw=False, session=None):
        self.mtda.debug(3, "main.console_send()")

        self._check_expired(session)
        result = None
        if self.console_locked(session) == False and self.console_logger is not None:
            result = self.console_logger.write(data, raw)

        self.mtda.debug(3, "main.console_send(): %s" % str(result))
        return result

    def console_tail(self, session=None):
        self.mtda.debug(3, "main.console_tail()")

        self._check_expired(session)
        if self.console_locked(session) == False and self.console_logger is not None:
            result = self.console_logger.tail()

        self.mtda.debug(3, "main.console_tail(): %s" % str(result))
        return result

    def debug(self, level, msg):
        if self.debug_level >= level:
            if self.debug_level == 0:
                prefix = "# "
            else:
                prefix = "# debug%d: " % level
            msg = str(msg).replace("\n", "\n%s ... " % prefix)
            lines = msg.splitlines()
            for line in lines:
                line = _make_printable(line)
                print("%s%s" % (prefix, line), file=sys.stderr)

    def env_get(self, name, session=None):
        self.mtda.debug(3, "env_get()")

        self._check_expired(session)
        result = None
        if name in self.env:
            result = self.env[name]

        self.mtda.debug(3, "env_get(): %s" % str(result))
        return result

    def env_set(self, name, value, session=None):
        self.mtda.debug(3, "env_set()")

        self._check_expired(session)
        result = None
        if name in self.env:
            result = self.env[name]
        self.env[name] = value

        self.mtda.debug(3, "env_set(): %s" % str(result))
        return result

    def keyboard_write(self, str, session=None):
        self.mtda.debug(3, "main.keyboard_write()")

        self._check_expired(session)
        result = None
        if self.keyboard is not None:
            result = self.keyboard.write(str)

        self.mtda.debug(3, "main.keyboard_write(): %s" % str(result))
        return result

    def power_locked(self, session=None):
        self.mtda.debug(3, "main.power_locked()")

        self._check_expired(session)
        if self.power_controller is None:
            result = True
        else:
            result = self._check_locked(session)

        self.mtda.debug(3, "main.power_locked(): %s" % str(result))
        return result

    def storage_bytes_written(self, session=None):
        self.mtda.debug(3, "main.storage_bytes_written()")

        self._check_expired(session)
        result = self._storage_bytes_written

        self.mtda.debug(3, "main.storage_bytes_written(): %s" % str(result))
        return result

    def storage_close(self, session=None):
        self.mtda.debug(3, "main.storage_close()")

        self._check_expired(session)
        if self.sdmux_controller is None:
            result = False
        else:
            self.bz2dec = None
            self.zdec = None
            if self._storage_opened == True:
                self._storage_opened = not self.sdmux_controller.close()
            result = (self._storage_opened == False)

        self.mtda.debug(3, "main.storage_close(): %s" % str(result))
        return result

    def storage_locked(self, session=None):
        self.mtda.debug(3, "main.storage_locked()")

        self._check_expired(session)
        if self._check_locked(session):
            result = True
        # Cannot swap the shared storage device between the host and target
        # without a driver
        elif self.sdmux_controller is None:
            self.mtda.debug(4, "storage_locked(): no shared storage device")
            result = True
        # If hotplugging is supported, swap only if the shared storage isn't opened
        elif self.sdmux_controller.supports_hotplug() == True:
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
        elif self._storage_opened == True:
            self.mtda.debug(4, "storage_locked(): shared storage is in used (opened)")
            result = True
        # We may otherwise swap our shared storage device
        else:
            result = False

        self.mtda.debug(3, "main.storage_locked(): %s" % str(result))
        return result

    def storage_mount(self, part=None, session=None):
        self.mtda.debug(3, "main.storage_mount()")

        self._check_expired(session)
        if self._storage_mounted == True:
            self.mtda.debug(4, "storage_mount(): already mounted")
            result = True
        elif self.sdmux_controller is None:
            self.mtda.debug(4, "storage_mount(): no shared storage device")
            return False
        else:
            result = self.sdmux_controller.mount(part)
            self._storage_mounted = (result == True)

        self.mtda.debug(3, "main.storage_mount(): %s" % str(result))
        return result

    def storage_update(self, dst, offset, data, session=None):
        self.mtda.debug(3, "main.storage_update()")

        self._check_expired(session)
        if self.sdmux_controller is None:
            self.mtda.debug(4, "storage_update(): no shared storage device")
            result = -1
        elif offset == 0:
            self._storage_bytes_written = 0
        result = self.sdmux_controller.update(dst, offset, data)
        if result > 0:
            self._storage_bytes_written = self._storage_bytes_written + result

        self.mtda.debug(3, "main.storage_update(): %s" % str(result))
        return result

    def storage_open(self, session=None):
        self.mtda.debug(3, "main.storage_open()")

        self._check_expired(session)
        if self.sdmux_controller is None:
            self.mtda.debug(4, "storage_open(): no shared storage device")
            result = False
        else:
            self.storage_close()
            self._storage_bytes_written = 0
            result = self.sdmux_controller.open()
            self._storage_opened = (result == True)

        self.mtda.debug(3, "main.storage_open(): %s" % str(result))
        return result

    def storage_status(self, session=None):
        self.mtda.debug(3, "main.storage_status()")

        self._check_expired(session)
        if self.sdmux_controller is None:
            self.mtda.debug(4, "storage_status(): no shared storage device")
            result = "???"
        else:
            result = self.sdmux_controller.status()

        self.mtda.debug(3, "main.storage_status(): %s" % str(result))
        return result

    def _storage_write_bz2(self, data):
        self.mtda.debug(3, "main._storage_write_bz2()")

        # Decompress and write the newly received data
        uncompressed = self.bz2dec.decompress(data, self.blksz)
        result = self.sdmux_controller.write(uncompressed)
        if result == False:
            result = -1
        else:
            self._storage_bytes_written += len(uncompressed)

            # Check if we can write more data without further input
            if self.bz2dec.needs_input == False:
                result = 0
            else:
                # Data successfully uncompressed and written to the shared storage device
                result = self.blksz

        self.mtda.debug(3, "main._storage_write_bz2(): %s" % str(result))
        return result

    def storage_write_bz2(self, data, session=None):
        self.mtda.debug(3, "main.storage_write_bz2()")

        self._check_expired(session)
        if self.sdmux_controller is None:
            result = -1
        else:
            # Create a bz2 decompressor when called for the first time
            if self.bz2dec is None:
                self.bz2dec = bz2.BZ2Decompressor()

            cont   = True
            start  = time.monotonic()
            result = -1

            while cont == True:
                # Decompress and write newly received data
                try:
                    # Uncompress and write data
                    result = self._storage_write_bz2(data)
                    if result != 0:
                        # Either got an error or needing more data; escape from
                        # this loop to provide feedback
                        cont = False
                    else:
                        # Check if this loop has been running for quite some time,
                        # in which case we would to give our client an update
                        now = time.monotonic()
                        if (now - start) >= self.fbintvl:
                            cont = False
                        # If we should continue and do not need more data at this time,
                        # use an empty buffer for the next iteration
                        elif result == 0:
                            data = b''
                except EOFError:
                    # Handle multi-streams: create a new decompressor and we will start
                    # with data unused from the previous decompressor
                    data = self.bz2dec.unused_data
                    self.bz2dec = bz2.BZ2Decompressor()
                    cont = (len(data) > 0) # loop only if we have unused data
                    result = 0             # we do not need more input data

        self.mtda.debug(3, "main.storage_write_bz2(): %s" % str(result))
        return result

    def _storage_write_gz(self, data):
        self.mtda.debug(3, "main._storage_write_gz()")

        # Decompress and write the newly received data
        uncompressed = self.zdec.decompress(data, self.blksz)
        status = self.sdmux_controller.write(uncompressed)
        if status == False:
            result = -1
        else:
            self._storage_bytes_written += len(uncompressed)

            # Check if we can write more data without further input
            if len(self.zdec.unconsumed_tail) > 0:
                result = 0
            else:
               # Data successfully uncompressed and written to the shared storage device
                result = self.blksz

        self.mtda.debug(3, "main._storage_write_gz(): %s" % str(result))
        return result

    def storage_write_gz(self, data, session=None):
        self.mtda.debug(3, "main.storage_write_gz()")

        self._check_expired(session)
        if self.sdmux_controller is None:
            result = -1
        else:
            # Create a zlib decompressor when called for the first time
            if self.zdec is None:
                self.zdec = zlib.decompressobj(16+zlib.MAX_WBITS)

            # Check if we should use unconsumed data from the previous call
            if len(data) == 0:
                data = self.zdata

            cont   = True
            start  = time.monotonic()
            result = -1

            while cont == True:
                # Decompress and write newly received data
                result = self._storage_write_gz(data)
                self.zdata = None
                if result != 0:
                    # Either got an error or needing more data; escape from
                    # this loop to provide feedback
                    cont = False
                else:
                    # If we should continue and do not need more data at this time,
                    # use the unconsumed data for the next iteration
                    data = self.zdec.unconsumed_tail
                    # Check if this loop has been running for quite some time,
                    # in which case we would to give our client an update
                    now = time.monotonic()
                    if (now - start) >= self.fbintvl:
                        self.zdata = data
                        cont = False

        self.mtda.debug(3, "main.storage_write_gz(): %s" % str(result))
        return result

    def storage_write_raw(self, data, session=None):
        self.mtda.debug(3, "main.storage_write_raw()")

        self._check_expired(session)
        if self.sdmux_controller is None:
            result = -1
        else:
            result = self.sdmux_controller.write(data)
            if result == False:
                resukt = -1
            else:
                self._storage_bytes_written += len(data)
                result = self.blksz

        self.mtda.debug(3, "main.storage_write_raw(): %s" % str(result))
        return result

    def storage_to_host(self, session=None):
        self.mtda.debug(3, "main.storage_to_host()")

        self._check_expired(session)
        if self.storage_locked(session) == False:
            result = self.sdmux_controller.to_host()
        else:
            self.mtda.debug(1, "storage_to_host(): shared storage is locked")
            result = False

        self.mtda.debug(3, "main.storage_to_host(): %s" % str(result))
        return result

    def storage_to_target(self, session=None):
        self.mtda.debug(3, "main.storage_to_target()")

        self._check_expired(session)
        if self.storage_locked(session) == False:
            self.storage_close()
            result = self.sdmux_controller.to_target()
        else:
            self.mtda.debug(1, "storage_to_target(): shared storage is locked")
            result = False

        self.mtda.debug(3, "main.storage_to_target(): %s" % str(result))
        return result

    def storage_swap(self, session=None):
        self.mtda.debug(3, "main.storage_swap()")

        self._check_expired(session)
        if self.storage_locked(session) == False:
            result = self.storage_status(session)
            if result == self.sdmux_controller.SD_ON_HOST:
                self.sdmux_controller.to_target()
            elif result == self.sdmux_controller.SD_ON_TARGET:
                self.sdmux_controller.to_host()
        result = self.storage_status(session)
        return result

        self.mtda.debug(3, "main.storage_swap(): %s" % str(result))
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

        self._check_expired(session)
        owner = self.target_owner()
        if owner is None or owner == session:
            self._lock_owner = session
            result = True
        else:
            result = False

        self.mtda.debug(3, "main.target_lock(): %s" % str(result))
        return result

    def target_locked(self, session):
        self.mtda.debug(3, "main.target_locked()")

        self._check_expired(session)
        return self._check_locked(session)

    def target_owner(self):
        self.mtda.debug(3, "main.target_owner()")

        return self._lock_owner

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
            self.mtda.debug(4, "exec_power_on_script(): %s" % self.power_on_script)
            result = exec(self.power_on_script, { "env" : self.env, "mtda" : self })

        self.mtda.debug(3, "main.exec_power_on_script(): %s" % str(result))
        return result

    def target_on(self, session=None):
        self.mtda.debug(3, "main.target_on()")

        if self.console_logger is not None:
           self.console_logger.resume()
        self._check_expired(session)
        result = False
        if self.power_locked(session) == False:
            result = self.power_controller.on()
            if result == True:
                self.exec_power_on_script()

        self.mtda.debug(3, "main.target_on(): %s" % str(result))
        return result

    def exec_power_off_script(self):
        self.mtda.debug(3, "main.exec_power_off_script()")

        if self.power_off_script:
            exec(self.power_off_script, { "env" : self.env, "mtda" : self })

    def target_off(self, session=None):
        self.mtda.debug(3, "main.target_off()")

        result = False
        self._check_expired(session)
        if self.power_locked(session) == False:
            result = self.power_controller.off()
            if self.console_logger is not None:
                self.console_logger.reset_timer()
                if result == True:
                    self.console_logger.pause()
                    self.exec_power_off_script()

        self.mtda.debug(3, "main.target_off(): %s" % str(result))
        return result

    def target_status(self, session=None):
        self.mtda.debug(3, "main.target_status()")

        self._check_expired(session)
        if self.power_controller is None:
            result = "???"
        else:
            result = self.power_controller.status()

        self.mtda.debug(3, "main.target_status(): %s" % str(result))
        return result

    def target_toggle(self, session=None):
        self.mtda.debug(3, "main.target_toggle()")

        self._check_expired(session)
        if self.power_locked(session) == False:
            result = self.power_controller.toggle()
            if result == self.power_controller.POWER_ON:
                if self.console_logger is not None:
                    self.console_logger.resume()
                self.exec_power_on_script()
            elif result == self.power_controller.POWER_OFF:
                self.exec_power_off_script()
                if self.console_logger is not None:
                    self.console_logger.pause()
                    self.console_logger.reset_timer()
        else:
            result = self.power_controller.POWER_LOCKED

        self.mtda.debug(3, "main.target_toggle(): %s" % str(result))
        return result

    def target_unlock(self, session):
        self.mtda.debug(3, "main.target_unlock()")

        result = False
        self._check_expired(session)
        if self.target_owner() == session:
            self._lock_owner = None
            result = True

        self.mtda.debug(3, "main.target_unlock(): %s" % str(result))
        return result

    def usb_find_by_class(self, className, session=None):
        self.mtda.debug(3, "main.usb_find_by_class()")

        self._check_expired(session)
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

        self._check_expired(session)
        usb_switch = self.usb_find_by_class(className, session)
        return usb_switch is not None

    def usb_off(self, ndx, session=None):
        self.mtda.debug(3, "main.usb_off()")

        self._check_expired(session)
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                usb_switch.off()
        except IndexError:
            print("invalid USB switch #" + str(ndx), file=sys.stderr)

    def usb_off_by_class(self, className, session=None):
        self.mtda.debug(3, "main.usb_off_by_class()")

        self._check_expired(session)
        usb_switch = self.usb_find_by_class(className, session)
        if usb_switch is not None:
            return usb_switch.off()
        return False

    def usb_on(self, ndx, session=None):
        self.mtda.debug(3, "main.usb_on()")

        self._check_expired(session)
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                usb_switch.on()
        except IndexError:
            print("invalid USB switch #" + str(ndx), file=sys.stderr)

    def usb_on_by_class(self, className, session=None):
        self.mtda.debug(3, "main.usb_on_by_class()")

        self._check_expired(session)
        usb_switch = self.usb_find_by_class(className, session)
        if usb_switch is not None:
            return usb_switch.on()
        return False

    def usb_ports(self, session=None):
        self.mtda.debug(3, "main.usb_ports()")

        self._check_expired(session)
        return len(self.usb_switches)

    def usb_status(self, ndx, session=None):
        self.mtda.debug(3, "main.usb_status()")

        self._check_expired(session)
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

        self._check_expired(session)
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                usb_switch.toggle()
        except IndexError:
            print("invalid USB switch #" + str(ndx), file=sys.stderr)

    def load_config(self, remote=None, is_server=False):
        self.mtda.debug(3, "main.load_config()")

        self.remote = remote
        self.is_remote = remote is not None
        self.is_server = is_server
        parser = configparser.ConfigParser()
        configs_found = parser.read(self.config_files)
        if parser.has_section('main'):
            self.load_main_config(parser)
        if parser.has_section('remote'):
            self.load_remote_config(parser)
        if self.is_remote == False:
            if parser.has_section('power'):
                self.load_power_config(parser)
            if parser.has_section('console'):
                self.load_console_config(parser)
            if parser.has_section('keyboard'):
                self.load_keyboard_config(parser)
            if parser.has_section('sdmux'):
                self.load_sdmux_config(parser)
            if parser.has_section('usb'):
                self.load_usb_config(parser)
            if parser.has_section('scripts'):
                scripts = parser['scripts']
                self.power_on_script  = self._parse_script(scripts.get('power on', None))
                self.power_off_script = self._parse_script(scripts.get('power off', None))

    def load_main_config(self, parser):
        self.mtda.debug(3, "main.load_main_config()")

        self.mtda.debug_level = int(parser.get('main', 'debug', fallback=self.mtda.debug_level))

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
            self.console.configure(dict(parser.items('console')))
        except configparser.NoOptionError:
            print('console variant not defined!', file=sys.stderr)
        except ImportError:
            print('console "%s" could not be found/loaded!' % (variant), file=sys.stderr)

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
            self.keyboard.probe()
        except configparser.NoOptionError:
            print('keyboard controller variant not defined!', file=sys.stderr)
        except ImportError:
            print('keyboard controller "%s" could not be found/loaded!' % (variant), file=sys.stderr)

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
            print('power controller "%s" could not be found/loaded!' % (variant), file=sys.stderr)
    
    def load_sdmux_config(self, parser):
        self.mtda.debug(3, "main.load_sdmux_config()")

        try:
            # Get variant
            variant = parser.get('sdmux', 'variant')
            # Try loading its support class
            mod = importlib.import_module("mtda.sdmux." + variant)
            factory = getattr(mod, 'instantiate')
            self.sdmux_controller = factory(self)
            # Configure the sdmux controller
            self.sdmux_controller.configure(dict(parser.items('sdmux')))
        except configparser.NoOptionError:
            print('sdmux controller variant not defined!', file=sys.stderr)
        except ImportError:
            print('power controller "%s" could not be found/loaded!' % (variant), file=sys.stderr)

    def load_remote_config(self, parser):
        self.mtda.debug(3, "main.load_remote_config()")

        self.conport = int(parser.get('remote', 'console', fallback=self.conport))
        self.ctrlport = int(parser.get('remote', 'control', fallback=self.ctrlport))
        if self.is_server == False:
            if self.remote is None:
                # Load remote setting from the configuration
                self.remote = parser.get('remote', 'host', fallback=self.remote)
                # Allow override from the environment
                self.remote = os.getenv('MTDA_REMOTE', self.remote)
        else:
            self.remote = None
        self.is_remote = self.remote is not None

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
            print('usb switch "%s" could not be found/loaded!' % (variant), file=sys.stderr)

    def start(self):
        self.mtda.debug(3, "main.start()")

        if self.is_remote == True:
            return True

        # Probe the specified power controller
        if self.power_controller is not None:
            status = self.power_controller.probe()
            if status == False:
                print('Probe of the Power Controller failed!', file=sys.stderr)
                return False

        # Probe the specified sdmux controller
        if self.sdmux_controller is not None:
            status = self.sdmux_controller.probe()
            if status == False:
                print('Probe of the shared storage device failed!', file=sys.stderr)
                return False

        if self.console is not None:
            # Create a publisher
            if self.is_server == True:
                context = zmq.Context()
                socket = context.socket(zmq.PUB)
                socket.bind("tcp://*:%s" % self.conport)
            else:
                socket = None

            # Create and start console logger
            status = self.console.probe()
            if status == False:
                print('Probe of the %s console failed!' % self.console.variant, file=sys.stderr)
                return False
            self.console_logger = ConsoleLogger(self, self.console, socket, self.power_controller)
            self.console_logger.start()

        return True

    def _check_expired(self, session):
        self.mtda.debug(3, "main._check_expired()")

        if self._lock_owner:
            now = time.monotonic()
            if session == self._lock_owner:
                self._lock_expiry = now + (self._lock_timeout * 60)
            elif now >= self._lock_expiry:
                self._lock_owner = None

    def _check_locked(self, session):
        self.mtda.debug(3, "main._check_locked()")

        owner = self.target_owner()
        if owner is None:
            return False
        status = False if session == owner else True
        return status
