# System imports
import abc
import os
import sys
import tempfile
import threading
import time

# Local imports
from mtda.power.controller import PowerController

class QemuController(PowerController):

    def __init__(self):
        self.dev        = None
        self.ev         = threading.Event()
        self.bios       = None
        self.cpu        = None
        self.executable = "qemu-system-x86_64"
        self.machine    = None
        self.memory     = 512
        self.pid        = None
        self.storage    = None

    def configure(self, conf):
        """ Configure this power controller from the provided configuration"""
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
           self.storage = conf['storage']

    def probe(self):
        if self.executable is None:
            raise ValueError("qemu executable not specified!")
        result = os.system("%s --version" % self.executable)
        if result != 0:
            raise ValueError("could not execute %s!" % self.executable)

    def start(self):
        if self.pid is not None:
            return True
        if os.path.exists("/tmp/qemu-mtda.in"):
            os.unlink("/tmp/qemu-mtda.in")
        if os.path.exists("/tmp/qemu-mtda.out"):
            os.unlink("/tmp/qemu-mtda.out")
        os.mkfifo("/tmp/qemu-mtda.in")
        os.mkfifo("/tmp/qemu-mtda.out")
        self.pidfile = tempfile.NamedTemporaryFile(delete=False).name

        # base options
        options  = "-daemonize -pidfile %s -S -m %d" % (self.pidfile, self.memory)
        options += " -chardev pipe,id=monitor,path=/tmp/qemu-mtda -monitor chardev:monitor"
        options += " -usb"

        # extra options
        if self.bios is not None:
            options += " -L /usr/share/qemu-efi"
            options += " -bios %s" % self.bios
        if self.cpu is not None:
            options += " -cpu %s" % self.cpu
        if self.machine is not None:
            options += " -machine %s" % self.machine
        if self.storage is not None:
            options += " -drive file=%s,media=disk,format=raw" % self.storage

        sys.stderr.write("%s %s\n" % (self.executable, options))
        result = os.system("%s %s" % (self.executable, options))
        if result == 0:
            with open(self.pidfile, "r") as f:
                self.pid = f.read()
            os.unlink(self.pidfile)
            return True
        return False

    def monitor_output(self):
        fd = os.open("/tmp/qemu-mtda.out", os.O_RDONLY)
        os.set_blocking(fd, False)
        tries = 10
        output = ""
        while tries > 0:
            try:
                output += os.read(fd, 2048).decode('utf-8')
            except BlockingIOError:
                tries = tries - 1
                time.sleep(0.25)
        os.close(fd)
        return output

    def cmd(self, what):
        started = self.start()
        if started == False:
            return None

        # flush monitor output
        self.monitor_output()

        # send requested command to "out" pipe
        with open("/tmp/qemu-mtda.in", "w") as f:
            f.write("%s\n" % what)

        # provide response from the monitor
        output = self.monitor_output()
        return output

    def on(self):
        """ Power on the attached device"""
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
        """ Power off the attached device"""
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
        """ Determine the current power state of the attached device"""
        lines = self.cmd('info status').splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith("VM status:"):
                if 'running' in line:
                    return self.POWER_ON
                if 'paused' in line:
                    return self.POWER_OFF
        return self.POWER_UNSURE

    def toggle(self):
        """ Toggle power for the attached device"""
        s = self.status()
        if s == self.POWER_OFF:
            self.on()
        else:
            self.off()
        return self.status()

    def wait(self):
        while self.status() != self.POWER_ON:
            self.ev.wait()

def instantiate():
   return QemuController()
