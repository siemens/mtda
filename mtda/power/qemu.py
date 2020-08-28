# System imports
import abc
import atexit
import os
import pathlib
import psutil
import signal
import sys
import tempfile
import threading
import time

# Local imports
from mtda.power.controller import PowerController

class QemuController(PowerController):

    def __init__(self, mtda):
        self.dev        = None
        self.ev         = threading.Event()
        self.bios       = None
        self.cpu        = None
        self.executable = "kvm"
        self.lock       = threading.Lock()
        self.machine    = None
        self.memory     = 512
        self.mtda       = mtda
        self.pidOfQemu  = None
        self.pidOfSwTpm = None
        self.storage    = None
        self.swtpm      = "/usr/bin/swtpm"
        self.watchdog   = None

    def configure(self, conf):
        self.mtda.debug(3, "power.qemu.configure()")

        if 'bios' in conf:
           self.bios = conf['bios']
        if 'cpu' in conf:
           self.cpu = conf['cpu']
        if 'executable' in conf:
           self.executable = conf['executable']
        if 'machine' in conf:
           self.machine = conf['machine']
        if 'memory' in conf:
           self.memory = int(conf['memory'])
        if 'storage' in conf:
           self.storage = os.path.realpath(conf['storage'])
        if 'swtpm' in conf:
           self.swtpm = os.path.realpath(conf['swtpm'])
        if 'watchdog' in conf:
           self.watchdog = conf['watchdog']
        elif os.path.exists(self.swtpm) == False:
            self.swtpm = None

    def probe(self):
        self.mtda.debug(3, "power.qemu.probe()")

        if self.executable is None:
            raise ValueError("qemu executable not specified!")
        result = os.system("%s --version" % self.executable)
        if result != 0:
            raise ValueError("could not execute %s!" % self.executable)
        if self.swtpm is not None and os.path.exists(self.swtpm) == False:
            raise ValueError("swtpm (%s) could not be found!" % self.swtpm)

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
        self.pidfile = tempfile.NamedTemporaryFile(delete=False).name

        # base options
        options  = "-daemonize -pidfile %s -S -m %d" % (self.pidfile, self.memory)
        options += " -chardev pipe,id=monitor,path=/tmp/qemu-mtda -monitor chardev:monitor"
        options += " -serial pipe:/tmp/qemu-serial"
        options += " -usb"
        options += " -vnc :0"

        # extra options
        if self.bios is not None:
            options += " -bios %s" % self.bios
        if self.cpu is not None:
            options += " -cpu %s" % self.cpu
        if self.machine is not None:
            options += " -machine %s" % self.machine
        if self.storage is not None:
            options += " -drive file=%s,media=disk,format=raw" % self.storage
            if os.path.exists(self.storage) == False:
                sparse = pathlib.Path(self.storage)
                sparse.touch()
                os.truncate(str(sparse), 16*1024*1024*1024)
        if self.watchdog is not None:
            options += " -watchdog %s" % self.watchdog

        # swtpm options
        if self.swtpm is not None:
            os.makedirs("/tmp/qemu-swtpm", exist_ok=True)
            result = os.system(self.swtpm
                      + " socket -d"
                      + " --tpmstate dir=/tmp/qemu-swtpm"
                      + " --ctrl type=unixio,path=/tmp/qemu-swtpm/sock"
                      + " --pid file=%s --tpm2" % self.pidfile)
            if result == 0:
                with open(self.pidfile, "r") as f:
                    self.pidOfSwTpm = int(f.read())
                self.mtda.debug(2, "power.qemu.start(): swtpm process started [%d]" % self.pidOfSwTpm)

                options += " -chardev socket,id=chrtpm,path=/tmp/qemu-swtpm/sock"
                options += " -tpmdev emulator,id=tpm0,chardev=chrtpm"
                options += " -device tpm-tis,tpmdev=tpm0"

        result = os.system("%s %s" % (self.executable, options))
        if result == 0:
            with open(self.pidfile, "r") as f:
                self.pidOfQemu = int(f.read())
            self.mtda.debug(2, "power.qemu.start(): qemu process started [%d]" % self.pidOfQemu)
            os.unlink(self.pidfile)
            atexit.register(self.stop)
            return True
        return False

    def stop(self):
        self.mtda.debug(3, "power.qemu.stop()")

        self.lock.acquire()
        result = True

        if self.pidOfQemu is not None:

            with open("/tmp/qemu-mtda.in", "w") as f:
                f.write("quit\n")

            result = False
            timeout = 3
            while timeout > 0 and psutil.pid_exists(self.pidOfQemu):
                self.mtda.debug(2, "power.qemu.stop(): waiting %d more seconds for qemu to terminate" % timeout)
                time.sleep(1)
                timeout = timeout - 1
            if psutil.pid_exists(self.pidOfQemu):
                self.mtda.debug(2, "power.qemu.stop(): terminating qemu using SIGTERM (%d)" % self.pidOfQemu)
                os.kill(self.pidOfQemu, signal.SIGTERM)
                time.sleep(1)
            if psutil.pid_exists(self.pidOfQemu) == False:
                result = True
                self.pidOfQemu = None

        if self.pidOfSwTpm is not None:
            if psutil.pid_exists(self.pidOfSwTpm):
                self.mtda.debug(2, "power.qemu.stop(): terminating swtpm using SIGTERM (%d)" % self.pidOfSwTpm)
                os.kill(self.pidOfSwTpm, signal.SIGTERM)
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
        while output.endswith("(qemu) ") == False:
            output += self.monitor_output_non_blocking()
        return output

    def cmd(self, what):
        self.mtda.debug(3, "power.qemu.cmd()")

        started = self.start()
        if started == False:
            return None

        # serialize commands to the monitor
        self.lock.acquire()

        # flush monitor output
        self.monitor_output_non_blocking()

        # send requested command to "out" pipe
        with open("/tmp/qemu-mtda.in", "w") as f:
            f.write("%s\n" % what)

        # provide response from the monitor
        output = self.monitor_command_output()

        self.lock.release()
        return output

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
            self.ev.set()
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

    def wait(self):
        self.mtda.debug(3, "power.qemu.wait()")

        while self.status() != self.POWER_ON:
            self.ev.wait()

def instantiate(mtda):
   return QemuController(mtda)
