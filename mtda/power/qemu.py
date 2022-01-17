# ---------------------------------------------------------------------------
# QEMU power driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import atexit
import os
import pathlib
import psutil
import re
import signal
import tempfile
import threading
import time

# Local imports
from mtda.power.controller import PowerController


class QemuController(PowerController):

    def __init__(self, mtda):
        self.dev = None
        self.ev = threading.Event()
        self.bios = None
        self.cpu = None
        self.drives = []
        self.executable = "kvm"
        self.hostname = "mtda-kvm"
        self.lock = threading.Lock()
        self.machine = None
        self.memory = 512
        self.mtda = mtda
        self.pflash_ro = None
        self.pflash_rw = None
        self.pidOfQemu = None
        self.pidOfSwTpm = None
        self.swtpm = "/usr/bin/swtpm"
        self.watchdog = None

    def configure(self, conf):
        self.mtda.debug(3, "power.qemu.configure()")

        if 'bios' in conf:
            self.bios = conf['bios']
        if 'cpu' in conf:
            self.cpu = conf['cpu']
        if 'executable' in conf:
            self.executable = conf['executable']
        if 'hostname' in conf:
            self.hostname = conf['hostname']
        if 'machine' in conf:
            self.machine = conf['machine']
        if 'memory' in conf:
            self.memory = int(conf['memory'])
        if 'pflash_ro' in conf:
            self.pflash_ro = os.path.realpath(conf['pflash_ro'])
        if 'pflash_rw' in conf:
            self.pflash_rw = os.path.realpath(conf['pflash_rw'])
        if 'storage' in conf and 'storage.0' not in conf:
            conf['storage.0'] = conf['storage']
        if 'swtpm' in conf:
            self.swtpm = os.path.realpath(conf['swtpm'])
        elif os.path.exists(self.swtpm) is False:
            self.swtpm = None
        if 'watchdog' in conf:
            self.watchdog = conf['watchdog']
        n = 0
        while True:
            key = 'storage.{}'.format(n)
            if key in conf:
                path = os.path.realpath(conf[key])
                self.drives.append(path)
                n = n + 1
            else:
                break

    def probe(self):
        self.mtda.debug(3, "power.qemu.probe()")

        if self.executable is None:
            raise ValueError("qemu executable not specified!")
        result = os.system("%s --version" % self.executable)
        if result != 0:
            raise ValueError("could not execute %s!" % self.executable)
        if self.swtpm is not None and os.path.exists(self.swtpm) is False:
            raise ValueError("swtpm (%s) could not be found!" % self.swtpm)

    def getpid(self, pidfile, timeout=30):
        result = 0
        while timeout > 0:
            with open(pidfile, "r") as f:
                data = f.read()
                if data:
                    result = int(data)
                    break
            time.sleep(1)
            timeout = timeout - 1
        return result

    def start(self):
        self.mtda.debug(3, "power.qemu.start()")

        if self.pidOfQemu is not None:
            return True
        if os.path.exists("/tmp/qemu-mtda.in"):
            os.unlink("/tmp/qemu-mtda.in")
        if os.path.exists("/tmp/qemu-mtda.out"):
            os.unlink("/tmp/qemu-mtda.out")
        if os.path.exists("/tmp/qemu-serial.in"):
            os.unlink("/tmp/qemu-serial.in")
        if os.path.exists("/tmp/qemu-serial.out"):
            os.unlink("/tmp/qemu-serial.out")
        os.mkfifo("/tmp/qemu-mtda.in")
        os.mkfifo("/tmp/qemu-mtda.out")
        os.mkfifo("/tmp/qemu-serial.in")
        os.mkfifo("/tmp/qemu-serial.out")

        atexit.register(self.stop)

        # base options
        options = "-daemonize -S -m %d" % self.memory
        options += " -chardev pipe,id=monitor,path=/tmp/qemu-mtda"
        options += " -monitor chardev:monitor"
        options += " -serial pipe:/tmp/qemu-serial"
        options += " -device e1000,netdev=net0"
        options += " -netdev user,id=net0,"
        options += "hostfwd=tcp::2222-:22,hostname={0}".format(self.hostname)
        options += " -usb"
        options += " -vnc :0"

        # extra options
        if self.bios is not None:
            options += " -bios %s" % self.bios
        if self.cpu is not None:
            options += " -cpu %s" % self.cpu
        if self.machine is not None:
            options += " -machine %s" % self.machine
        if self.pflash_ro is not None:
            if pathlib.Path(self.pflash_ro).is_file():
                if os.access(self.pflash_ro, os.R_OK):
                    options += " -drive if=pflash,format=raw,"
                    options += "readonly,file=%s" % self.pflash_ro
                else:
                    raise ValueError("Read-only pflash file (%s) "
                                     "cannot be read." % self.pflash_ro)
            else:
                raise ValueError("Read-only pflash file (%s) does not "
                                 "exist or is not a file." % self.pflash_ro)
        if self.pflash_rw is not None:
            try:
                options += " -drive if=pflash,format=raw,"
                options += "file=%s" % self.pflash_rw
                if pathlib.Path(self.pflash_rw).is_file():
                    if not os.access(self.pflash_rw, os.W_OK):
                        raise ValueError("Writeable pflash file (%s) has no "
                                         "write permission." % self.pflash_rw)
                else:
                    # This is probably recoverable, we'll create an empty file
                    # and trust the try/except to save us if the specified
                    # location isn't usable for some reason (e.g. the location
                    # is write protected or the specified file already exists
                    # as a directory or something).
                    #
                    # The existing OVMF fd file is ~2MB so we'll create our
                    # writeable copy at the same size.
                    sparse = pathlib.Path(self.pflash_rw)
                    sparse.touch()
                    os.truncate(str(sparse), 2*1024*1024)
            except Exception as e:
                raise ValueError("Writeable pflash file (%s) does not exist "
                                 "or is not a file and cannot be created: "
                                 "%s" % (self.pflash_rw, e))
        if len(self.drives) > 0:
            for drv in self.drives:
                options += " -drive file={},media=disk,format=raw".format(drv)
                if os.path.exists(drv) is False:
                    sparse = pathlib.Path(drv)
                    sparse.touch()
                    os.truncate(str(sparse), 16*1024*1024*1024)
        if self.watchdog is not None:
            options += " -watchdog %s" % self.watchdog

        # swtpm options
        if self.swtpm is not None:
            with tempfile.NamedTemporaryFile() as pidfile:
                os.makedirs("/tmp/qemu-swtpm", exist_ok=True)
                result = os.system(
                      self.swtpm
                      + " socket -d"
                      + " --tpmstate dir=/tmp/qemu-swtpm"
                      + " --ctrl type=unixio,path=/tmp/qemu-swtpm/sock"
                      + " --pid file=%s --tpm2" % pidfile.name)
                if result == 0:
                    self.pidOfSwTpm = self.getpid(pidfile.name)
                    self.mtda.debug(2, "power.qemu.start(): "
                                       "swtpm process started "
                                       "[{0}]".format(self.pidOfSwTpm))
                else:
                    self.mtda.debug(1, "power.qemu.start(): "
                                       "swtpm process failed "
                                       "({0})".format(result))
                    return False

                options += " -chardev socket,id=chrtpm,"
                options += "path=/tmp/qemu-swtpm/sock"
                options += " -tpmdev emulator,id=tpm0,chardev=chrtpm"
                options += " -device tpm-tis,tpmdev=tpm0"

        with tempfile.NamedTemporaryFile() as pidfile:
            options += " -pidfile {0}".format(pidfile.name)
            result = os.system("%s %s" % (self.executable, options))
            if result == 0:
                self.pidOfQemu = self.getpid(pidfile.name)
                self.mtda.debug(2, "power.qemu.start(): "
                                   "qemu process started "
                                   "[{0}]".format(self.pidOfQemu))
                return True
            else:
                self.mtda.debug(1, "power.qemu.start(): "
                                   "qemu process failed "
                                   "({0})".format(result))
        return False

    def kill(self, name, pid, wait_before_kill=True, timeout=3):
        tries = timeout
        while wait_before_kill and tries > 0 and psutil.pid_exists(pid):
            self.mtda.debug(2, "waiting {0} more seconds for {1} "
                               "[{2}] to terminate".format(timeout, name, pid))
            time.sleep(1)
            tries = tries - 1
        if psutil.pid_exists(pid):
            self.mtda.debug(2, "terminating {0} "
                               "[{1}] using SIGTERM".format(name, pid))
            os.kill(pid, signal.SIGTERM)
            tries = timeout
        while tries > 0 and psutil.pid_exists(pid):
            time.sleep(1)
            tries = tries - 1
        if psutil.pid_exists(pid):
            self.mtda.debug(2, "terminating {0} "
                               "[{1}] using SIGKILL".format(name, pid))
            os.kill(pid, signal.SIGKILL)
        return psutil.pid_exists(pid)

    def stop(self):
        self.mtda.debug(3, "power.qemu.stop()")

        self.lock.acquire()
        result = True

        if self.pidOfQemu is not None:

            with open("/tmp/qemu-mtda.in", "w") as f:
                f.write("quit\n")
            result = self.kill("qemu", self.pidOfQemu)
            if result:
                self.pidOfQemu = None

        if self.pidOfSwTpm is not None:
            result = self.kill("swtpm", self.pidOfSwTpm, False)
            if result:
                self.pidOfSwTpm = None

        self.lock.release()
        return result

    def monitor_output_non_blocking(self):
        self.mtda.debug(4, "power.qemu.monitor_output_non_blocking()")

        fd = os.open("/tmp/qemu-mtda.out", os.O_RDONLY)
        os.set_blocking(fd, False)
        try:
            output = os.read(fd, 2048).decode('utf-8')
        except BlockingIOError:
            output = ""
        os.close(fd)
        return output

    def monitor_command_output(self):
        self.mtda.debug(3, "power.qemu.monitor_command_output()")

        output = ""
        while output.endswith("(qemu) ") is False:
            output += self.monitor_output_non_blocking()
        if output.endswith("(qemu) "):
            output = output[:-7]

        self.mtda.debug(3, "power.qemu.monitor_command_output(): %s" % output)
        return output

    def _cmd(self, what):
        self.mtda.debug(3, "power.qemu._cmd()")

        started = self.start()
        if started is False:
            return None

        # flush monitor output
        self.monitor_output_non_blocking()

        # send requested command to "out" pipe
        what += "\n"
        with open("/tmp/qemu-mtda.in", "w") as f:
            f.write(what)

        # provide response from the monitor
        output = self.monitor_command_output()

        self.mtda.debug(3, "power.qemu._cmd(): %s" % str(output))
        return output

    def cmd(self, what):
        self.mtda.debug(3, "power.qemu.cmd()")

        self.lock.acquire()
        result = self._cmd(what)
        self.lock.release()

        self.mtda.debug(3, "power.qemu.cmd(): %s" % str(result))
        return result

    def command(self, args):
        self.mtda.debug(3, "power.qemu.command()")

        result = self.cmd(" ".join(args))
        result = "\n".join(result.splitlines()[1:])

        self.mtda.debug(3, "power.qemu.command(): %s" % str(result))
        return result

    def on(self):
        self.mtda.debug(3, "power.qemu.on()")

        s = self.status()
        if s == self.POWER_ON:
            return True
        self.cmd("system_reset")
        self.cmd("cont")
        s = self.status()
        if s == self.POWER_ON:
            self.ev.set()
            return True
        return False

    def off(self):
        self.mtda.debug(3, "power.qemu.off()")

        s = self.status()
        if s == self.POWER_OFF:
            return True
        self.cmd("stop")
        self.cmd("system_reset")
        s = self.status()
        if s == self.POWER_OFF:
            self.ev.clear()
            return True
        return False

    def status(self):
        self.mtda.debug(3, "power.qemu.status()")

        result = self.POWER_UNSURE
        status = self.cmd('info status')
        if status is not None:
            for line in status.splitlines():
                line = line.strip()
                if line.startswith("VM status:"):
                    if 'running' in line:
                        result = self.POWER_ON
                    elif 'paused' in line:
                        result = self.POWER_OFF
                    break

        if result == self.POWER_UNSURE:
            self.mtda.debug(1, "unknown power status: %s" % str(status))

        self.mtda.debug(3, "power.qemu.status(): %s" % str(result))
        return result

    def toggle(self):
        self.mtda.debug(3, "power.qemu.toggle()")

        s = self.status()
        if s == self.POWER_OFF:
            self.on()
        else:
            self.off()
        return self.status()

    def usb_ids(self):
        info = self._cmd("info usb")
        lines = info.splitlines()
        results = []
        for line in lines:
            line = line.strip()
            if line.startswith("Device "):
                self.mtda.debug(2, "power.qemu.usb_ids(): {0}".format(line))
                match = re.findall(r'ID: (\S+)$', line)
                if match:
                    results.append(match[0])
        return results

    def usb_add(self, id, file):
        self.mtda.debug(3, "power.qemu.usb_add()")

        result = None
        self.lock.acquire()

        if id not in self.usb_ids():
            self.mtda.debug(2, "power.qemu.usb_add(): "
                               "adding '{0}' as '{1}'".format(file, id))
            cmdstr = "drive_add 0 if=none,id={0},file={1}"
            output = self._cmd(cmdstr.format(id, file))
            added = False
            reason = "drive_add failed"
            for line in output.splitlines():
                line = line.strip()
                if line == "OK":
                    added = True
                    break
            if added is True:
                reason = "device_add failed"
                cmdstr = "device_add usb-storage,id={0},drive={0},removable=on"
                self._cmd(cmdstr.format(id))
                added = (id in self.usb_ids())
            if added is True:
                result = id
                self.mtda.debug(2, "power.qemu.usb_add(): "
                                   "usb-storage '{0}' connected".format(id))
            else:
                self.mtda.debug(1, "power.qemu.usb_add(): "
                                   "usb-storage '{0}' could not be added "
                                   "({1})!".format(id, reason))

        self.mtda.debug(3, "power.qemu.usb_add(): %s" % str(result))
        self.lock.release()
        return result

    def usb_rm(self, id):
        self.mtda.debug(3, "power.qemu.usb_rm()")

        result = True
        self.lock.acquire()

        if id in self.usb_ids():
            self._cmd("device_del {0}".format(id))
            result = (id not in self.usb_ids())
            if result:
                self.mtda.debug(2, "power.qemu.usb_rm(): "
                                   "usb-storage '{0}' removed".format(id))
            else:
                self.mtda.debug(1, "power.qemu.usb_rm(): "
                                   "usb-storage '{0}' could not be "
                                   "removed!".format(id))

        self.mtda.debug(3, "power.qemu.usb_rm(): %s" % str(result))
        self.lock.release()
        return result

    def wait(self):
        self.mtda.debug(3, "power.qemu.wait()")

        while self.status() != self.POWER_ON:
            self.ev.wait()


def instantiate(mtda):
    return QemuController(mtda)
