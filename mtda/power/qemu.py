# ---------------------------------------------------------------------------
# QEMU power driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2026 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import atexit
import json
import os
import pathlib
import psutil
import socket
import subprocess
import tempfile
import threading
import time
import multiprocessing
import uuid

# Local imports
from mtda.power.controller import PowerController
from mtda.utils import Size, System


def _runtime_dir():
    return os.environ.get("XDG_RUNTIME_DIR", tempfile.gettempdir())


class QemuController(PowerController):

    def __init__(self, mtda):
        self.dev = None
        self.bios = None
        self.cpu = None
        self.smp = None
        self.drives = []
        self.efi_conf = {}
        self.usb_bootindex = 100
        self.executable = "kvm"
        self.firmware_state_file = "/var/lib/mtda/qemu-firmware"
        self.hostname = "mtda-kvm"
        self.legacy_conf = {}
        # re-entrant: usb_add()/usb_rm() hold the lock across several
        # qmp() calls, and qmp() itself locks
        self.lock = threading.RLock()
        self.machine = None
        self.memory = Size.to_bytes(512, 'MiB')
        self.mtda = mtda
        self.novnc = "/usr/share/novnc"
        self.pflash_ro = None
        self.pflash_rw = None
        self.firmware_mode = None
        self.pidOfQemu = None
        self.pidOfSwTpm = None
        self.pidOfWebsockify = None
        self.swtpm = "/usr/bin/swtpm"
        self.uuid = None
        self.watchdog = None
        self.websockify = "/usr/bin/websockify"
        self._qmp_sock = None
        self._qmp_file = None
        self._usb_devices = set()

        runtime_dir = _runtime_dir()
        self._qmp_socket = os.path.join(runtime_dir, "qemu-mtda.qmp")
        self._serial_base = os.path.join(runtime_dir, "qemu-serial")
        self.serial_in = self._serial_base + ".in"
        self.serial_out = self._serial_base + ".out"
        self._swtpm_dir = os.path.join(runtime_dir, "qemu-swtpm")
        self._swtpm_sock = os.path.join(self._swtpm_dir, "sock")

    def configure(self, conf):
        self.mtda.debug(3, "power.qemu.configure()")

        if 'bios' in conf:
            self.bios = conf['bios']
        if 'cpu' in conf:
            self.cpu = conf['cpu']
        if 'smp' in conf:
            self.smp = int(conf['smp'])
        if 'executable' in conf:
            self.executable = conf['executable']
        if 'hostname' in conf:
            self.hostname = conf['hostname']
        if 'machine' in conf:
            self.machine = conf['machine']
        if 'memory' in conf:
            self.memory = Size.to_bytes(conf['memory'], 'MiB')
        if 'pflash_ro' in conf:
            self.pflash_ro = os.path.realpath(conf['pflash_ro'])
        if 'pflash_rw' in conf:
            self.pflash_rw = os.path.realpath(conf['pflash_rw'])
        if 'storage' in conf and 'storage.0' not in conf:
            conf['storage.0'] = conf['storage']
        if 'storage.size' in conf and 'storage.0.size' not in conf:
            conf['storage.0.size'] = Size.to_bytes(conf['storage.size'], 'GiB')
        if 'swtpm' in conf:
            self.swtpm = os.path.realpath(conf['swtpm'])
        elif os.path.exists(self.swtpm) is False:
            self.swtpm = None
        if 'uuid' in conf:
            try:
                self.uuid = str(uuid.UUID(conf['uuid']))
            except ValueError:
                raise ValueError(f"invalid UUID: {conf['uuid']}")
        if 'watchdog' in conf:
            self.watchdog = conf['watchdog']
        n = 0
        while True:
            key = f'storage.{n}'
            sizekey = f'storage.{n}.size'
            if key in conf:
                path = os.path.realpath(conf[key])
                size = Size.to_bytes(conf[sizekey], 'GiB') if sizekey in conf else 16 * 1024**3
                self.drives.append((path, size))
                n = n + 1
            else:
                break

    def configure_firmware(self, parser):
        self.mtda.debug(3, "power.qemu.configure_firmware()")

        if parser.has_section('efi'):
            self.efi_conf = dict(parser.items('efi'))
        elif self.pflash_ro or self.pflash_rw:
            # backward compat: flat pflash_ro/pflash_rw under [power]
            self.efi_conf = {k: v for k, v in
                             (('pflash_ro', self.pflash_ro),
                              ('pflash_rw', self.pflash_rw)) if v}

        if parser.has_section('legacy'):
            self.legacy_conf = dict(parser.items('legacy'))
        elif self.bios:
            self.legacy_conf = {'bios': self.bios}

        default = None
        if parser.has_section('firmware'):
            default = parser.get('firmware', 'default', fallback=None)
            if default is not None and default not in ('efi', 'legacy'):
                raise ValueError(f"unsupported firmware default: {default}")
            if default == 'efi' and not self.efi_conf:
                raise ValueError(
                    "firmware default is 'efi' but no [efi] section "
                    "(or pflash_ro/pflash_rw) is configured")
        if default is None:
            # default to efi unless only legacy is configured
            default = 'legacy' if (self.legacy_conf and not self.efi_conf) \
                else 'efi'

        self.firmware_mode = self._load_firmware_state() or default
        self._apply_firmware(self.firmware_mode)

    def _load_firmware_state(self):
        if os.path.exists(self.firmware_state_file):
            with open(self.firmware_state_file, "r") as f:
                mode = f.read().strip()
                if mode in ('efi', 'legacy'):
                    return mode
        return None

    def _apply_firmware(self, mode):
        self.mtda.debug(3, f"power.qemu._apply_firmware({mode})")

        if mode == 'efi':
            conf = self.efi_conf
            self.bios = None
            ro = conf.get('pflash_ro')
            rw = conf.get('pflash_rw')
            self.pflash_ro = os.path.realpath(ro) if ro else None
            self.pflash_rw = os.path.realpath(rw) if rw else None
        else:
            conf = self.legacy_conf
            self.pflash_ro = None
            self.pflash_rw = None
            bios = conf.get('bios')
            self.bios = os.path.realpath(bios) if bios else None

    def firmware(self, mode=None):
        self.mtda.debug(3, "power.qemu.firmware()")

        if mode is not None and mode != self.firmware_mode:
            if mode not in ('efi', 'legacy'):
                raise ValueError(f"unsupported firmware mode: {mode}")
            if mode == 'efi' and not self.efi_conf:
                raise ValueError(
                    "efi firmware is not configured (add an [efi] "
                    "section with pflash_ro/pflash_rw)")
            self.firmware_mode = mode
            self._apply_firmware(mode)
            os.makedirs("/var/lib/mtda", exist_ok=True)
            with open(self.firmware_state_file, "w") as f:
                f.write(mode + "\n")

            # the new firmware only takes effect on the next qemu launch;
            # restart it now if it is already running
            if self.pidOfQemu is not None:
                self.mtda.debug(2, "power.qemu.firmware(): "
                                   f"restarting qemu for {mode} firmware")
                # start() unlinks and recreates the serial pipes, so any
                # console already attached to them needs to be closed and
                # reopened around the restart or it's left reading/writing
                # a stale (deleted) fifo
                logger = self.mtda.console_logger
                if logger is not None:
                    logger.pause()
                self.stop()
                self.start()
                if logger is not None:
                    logger.resume()

        return self.firmware_mode

    def probe(self):
        self.mtda.debug(3, "power.qemu.probe()")

        if self.executable is None:
            raise ValueError("qemu executable not specified!")
        result = os.system(f"{self.executable} --version")
        if result != 0:
            raise ValueError(f"could not execute {self.executable}!")
        if self.swtpm is not None and os.path.exists(self.swtpm) is False:
            raise ValueError(f"swtpm ({self.swtpm}) could not be found!")

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

    def getproc(self, cmd):
        for proc in psutil.process_iter():
            try:
                proccmd = " ".join(proc.cmdline())
                if proccmd.endswith(cmd):
                    return proc.pid
            except (psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess):
                pass
        return None

    def start(self):
        self.mtda.debug(3, "power.qemu.start()")

        if self.pidOfQemu is not None:
            return True
        self.usb_bootindex = 100
        if os.path.exists(self._qmp_socket):
            os.unlink(self._qmp_socket)
        if os.path.exists(self.serial_in):
            os.unlink(self.serial_in)
        if os.path.exists(self.serial_out):
            os.unlink(self.serial_out)
        os.mkfifo(self.serial_in)
        os.mkfifo(self.serial_out)

        atexit.register(self.stop)

        # base options
        options = f"-daemonize -S -m {int(self.memory / 1024**2)}"
        options += f" -qmp unix:{self._qmp_socket},server=on,wait=off"
        options += f" -serial pipe:{self._serial_base}"
        options += " -device e1000,netdev=net0"
        options += " -netdev user,id=net0,"
        options += f"hostfwd=tcp::2222-:22,hostname={self.hostname}"
        options += " -device qemu-xhci"
        options += " -device usb-tablet"
        options += " -vga virtio"
        options += " -vnc :0,websocket=on"
        options += " -boot menu=on,splash-time=5000"

        # extra options
        if self.bios is not None:
            options += f" -bios {self.bios}"
        if self.cpu is not None:
            options += f" -cpu {self.cpu}"
        if self.smp is not None:
            if self.smp == 0:
                options += f" -smp {multiprocessing.cpu_count()}"
            else:
                options += f" -smp {self.smp}"
        if self.machine is not None:
            options += f" -machine {self.machine}"
        if self.pflash_ro is not None:
            if pathlib.Path(self.pflash_ro).is_file():
                if os.access(self.pflash_ro, os.R_OK):
                    options += " -drive if=pflash,format=raw,"
                    options += f"readonly=on,file={self.pflash_ro}"
                else:
                    raise ValueError("Read-only pflash file (%s) "
                                     "cannot be read." % self.pflash_ro)
            else:
                raise ValueError("Read-only pflash file (%s) does not "
                                 "exist or is not a file." % self.pflash_ro)
        if self.pflash_rw is not None:
            try:
                options += " -drive if=pflash,format=raw,"
                options += f"file={self.pflash_rw}"
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
                    os.truncate(str(sparse), 2*1024**2)
            except Exception as e:
                raise ValueError("Writeable pflash file (%s) does not exist "
                                 "or is not a file and cannot be created: "
                                 "%s" % (self.pflash_rw, e))
        if len(self.drives) > 0:
            for n, (drv, size) in enumerate(self.drives):
                size = int(size / 1024**3)
                # bootindex can't be passed inline on a qcow2 -drive; split
                # into a backend (if=none) and an explicit ide-hd frontend
                # instead. Internal storage gets top priority (lowest index);
                # user needs to pick the USB drive from the firmware to boot
                # from it.
                options += f" -drive if=none,id=hd{n},format=qcow2,file={drv}"
                options += f" -device ide-hd,drive=hd{n},bootindex={n}"
                if os.path.exists(drv) is True:
                    cmd = ['qemu-img', 'info', drv]
                    info = subprocess.check_output(cmd, encoding="utf-8")
                    if 'qcow2' not in info:
                        os.unlink(drv)
                if os.path.exists(drv) is False:
                    subprocess.check_call(['qemu-img', 'create', '-f', 'qcow2',
                                           drv, f'{size}G'])
        if self.watchdog is not None:
            options += f" -device {self.watchdog},id=watchdog0"

        # UUID option
        vm_uuid = self.uuid
        if vm_uuid is None:
            uuid_file = "/var/lib/mtda/qemu-uuid"
            if os.path.exists(uuid_file):
                with open(uuid_file, "r") as f:
                    data = f.read().strip()
                try:
                    vm_uuid = str(uuid.UUID(data))
                except ValueError:
                    self.mtda.debug(1, "power.qemu.start(): "
                                       f"invalid UUID in {uuid_file}, "
                                       "generating a new one")
                    vm_uuid = None
            if not vm_uuid:
                vm_uuid = str(uuid.uuid4())
                os.makedirs("/var/lib/mtda", exist_ok=True)
                with open(uuid_file, "w") as f:
                    f.write(vm_uuid + "\n")
                self.mtda.debug(2, "power.qemu.start(): "
                                   f"generated UUID {vm_uuid}")
        options += f" -uuid {vm_uuid}"

        # swtpm options
        if self.swtpm is not None:
            with tempfile.NamedTemporaryFile() as pidfile:
                os.makedirs(self._swtpm_dir, exist_ok=True)
                result = os.system(
                      self.swtpm
                      + " socket -d"
                      + f" --tpmstate dir={self._swtpm_dir}"
                      + f" --ctrl type=unixio,path={self._swtpm_sock}"
                      + f" --pid file={pidfile.name} --tpm2")
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
                options += f"path={self._swtpm_sock}"
                options += " -tpmdev emulator,id=tpm0,chardev=chrtpm"
                options += " -device tpm-tis,tpmdev=tpm0"

        # Create a WebSocket proxy to QEMU's VNC service to support noVNC
        # when our web service is enabled and have websockify installed
        if os.path.exists(self.websockify):
            # bind on the same address as our web service
            cmd = self.websockify + " -D 0.0.0.0:5901 localhost:5900"
            result = os.system(cmd)
            if result == 0:
                self.pidOfWebsockify = self.getproc(cmd)
                self.mtda.debug(2, "power.qemu.start(): "
                                   "websockify process started "
                                   "[{0}]".format(self.pidOfWebsockify))

        with tempfile.NamedTemporaryFile() as pidfile:
            options += f" -pidfile {pidfile.name}"
            result = os.system(f"{self.executable} {options}")
            if result == 0:
                self.pidOfQemu = self.getpid(pidfile.name)
                self.mtda.debug(2, "power.qemu.start(): "
                                   "qemu process started "
                                   "[{0}]".format(self.pidOfQemu))
                if self._qmp_connect() is False:
                    self.mtda.debug(1, "power.qemu.start(): "
                                       "could not connect to QMP socket")
                    return False
                return True
            else:
                self.mtda.debug(1, "power.qemu.start(): "
                                   "qemu process failed "
                                   "({0})".format(result))
        return False

    def stop(self):
        self.mtda.debug(3, "power.qemu.stop()")

        self.lock.acquire()
        result = True

        if self._qmp_sock is not None:
            try:
                self._qmp_file.close()
                self._qmp_sock.close()
            except OSError:
                pass
            self._qmp_sock = None
            self._qmp_file = None
        self._usb_devices.clear()

        if self.pidOfQemu is not None:
            still_alive = System.kill("qemu", self.pidOfQemu)
            result = not still_alive
            if result:
                self.pidOfQemu = None

        if self.pidOfSwTpm is not None:
            still_alive = System.kill("swtpm", self.pidOfSwTpm)
            result = not still_alive
            if result:
                self.pidOfSwTpm = None

        if self.pidOfWebsockify is not None:
            still_alive = System.kill("websockify", self.pidOfWebsockify)
            result = not still_alive
            if result:
                self.pidOfWebsockify = None

        self.lock.release()
        return result

    def _qmp_send(self, msg):
        self._qmp_file.write(json.dumps(msg) + "\n")
        self._qmp_file.flush()

    def _qmp_recv(self):
        while True:
            line = self._qmp_file.readline()
            if not line:
                return None
            msg = json.loads(line)
            # events may be interleaved with command responses; only a
            # message without an "event" key answers the command we sent
            if "event" not in msg:
                return msg

    def _qmp_connect(self, timeout=30):
        self.mtda.debug(3, "power.qemu._qmp_connect()")

        sock = None
        while timeout > 0:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                sock.connect(self._qmp_socket)
                break
            except OSError:
                sock.close()
                sock = None
                time.sleep(1)
                timeout -= 1
        if sock is None:
            return False

        self._qmp_sock = sock
        self._qmp_file = sock.makefile(mode="rw")
        self._qmp_recv()  # greeting
        self._qmp_send({"execute": "qmp_capabilities"})
        self._qmp_recv()
        return True

    def qmp(self, command, arguments=None):
        self.mtda.debug(3, f"power.qemu.qmp({command})")

        with self.lock:
            started = self.start()
            if started is False:
                return None
            msg = {"execute": command}
            if arguments:
                msg["arguments"] = arguments
            self._qmp_send(msg)
            response = self._qmp_recv()

        if response is None:
            self.mtda.debug(1, f"power.qemu.qmp(): no response to '{command}'")
            return None
        if "error" in response:
            self.mtda.debug(1, "power.qemu.qmp(): "
                               f"'{command}' failed: {response['error']}")
            return None

        result = response.get("return")
        self.mtda.debug(3, f"power.qemu.qmp(): {result}")
        return result

    def on(self):
        self.mtda.debug(3, "power.qemu.on()")

        s = self.status()
        if s == self.POWER_ON:
            return True
        self.qmp("system_reset")
        self.qmp("cont")
        return self.status() == self.POWER_ON

    def off(self):
        self.mtda.debug(3, "power.qemu.off()")

        s = self.status()
        if s == self.POWER_OFF:
            return True
        self.qmp("stop")
        self.qmp("system_reset")
        return self.status() == self.POWER_OFF

    def status(self):
        self.mtda.debug(3, "power.qemu.status()")

        result = self.POWER_UNSURE
        info = self.qmp("query-status")
        if info is not None:
            result = self.POWER_ON if info.get("running") else self.POWER_OFF

        if result == self.POWER_UNSURE:
            self.mtda.debug(1, f"unknown power status: {str(info)}")

        self.mtda.debug(3, f"power.qemu.status(): {str(result)}")
        return result

    def usb_add(self, id, file):
        self.mtda.debug(3, "power.qemu.usb_add()")

        result = None
        with self.lock:
            if id not in self._usb_devices:
                self.mtda.debug(2, "power.qemu."
                                   f"usb_add(): adding '{file}' as '{id}'")
                info = subprocess.check_output(
                        ['qemu-img', 'info', '--output=json', file],
                        encoding="utf-8")
                fmt = json.loads(info)['format']

                reason = "blockdev-add failed"
                added = self.qmp("blockdev-add", {
                    "driver": fmt,
                    "node-name": id,
                    "file": {"driver": "file", "filename": file},
                }) is not None
                if added is True:
                    reason = "device_add failed"
                    added = self.qmp("device_add", {
                        "driver": "usb-storage",
                        "id": id,
                        "drive": id,
                        "removable": True,
                        "bootindex": self.usb_bootindex,
                    }) is not None
                    if added is False:
                        self.qmp("blockdev-del", {"node-name": id})
                if added is True:
                    result = id
                    self._usb_devices.add(id)
                    # hot-plugged devices need an explicit bootindex to be
                    # added to the firmware boot order (SeaBIOS/OVMF both
                    # read it from fw_cfg's bootorder, which is otherwise
                    # only populated from devices present at qemu startup)
                    self.usb_bootindex += 1
                    self.mtda.debug(2, "power.qemu.usb_add(): "
                                       "usb-storage '{0}' connected"
                                       .format(id))
                else:
                    self.mtda.debug(1, "power.qemu.usb_add(): "
                                       "usb-storage '{0}' could not be added "
                                       "({1})!".format(id, reason))

        self.mtda.debug(3, f"power.qemu.usb_add(): {str(result)}")
        return result

    def usb_rm(self, id):
        self.mtda.debug(3, "power.qemu.usb_rm()")

        result = True
        with self.lock:
            if id in self._usb_devices:
                result = self.qmp("device_del", {"id": id}) is not None
                if result:
                    if not self._qmp_wait_device_deleted(id):
                        self.mtda.debug(1, "power.qemu.usb_rm(): "
                                           f"'{id}' not confirmed removed, "
                                           "trying blockdev-del anyway")
                    self.qmp("blockdev-del", {"node-name": id})
                    self._usb_devices.discard(id)
                    self.mtda.debug(2, "power.qemu."
                                       f"usb_rm(): usb-storage '{id}' "
                                       "removed")
                else:
                    self.mtda.debug(1, "power.qemu.usb_rm(): "
                                       "usb-storage '{0}' could not be "
                                       "removed!".format(id))

        self.mtda.debug(3, f"power.qemu.usb_rm(): {str(result)}")
        return result

    def _qmp_wait_device_deleted(self, id, timeout=10):
        self.mtda.debug(3, f"power.qemu._qmp_wait_device_deleted({id})")

        self._qmp_sock.settimeout(timeout)
        try:
            while True:
                line = self._qmp_file.readline()
                if not line:
                    return False
                msg = json.loads(line)
                if (msg.get("event") == "DEVICE_DELETED"
                        and msg.get("data", {}).get("device") == id):
                    return True
        except socket.timeout:
            return False
        finally:
            self._qmp_sock.settimeout(None)


def instantiate(mtda):
    return QemuController(mtda)
