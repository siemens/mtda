# ---------------------------------------------------------------------------
# start/stop a docker container
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2024 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import atexit
import docker
import subprocess
import threading

# Local imports
from mtda.power.controller import PowerController


class DockerPowerController(PowerController):

    def __init__(self, mtda):
        self.mtda = mtda
        self._client = None
        self._command = "sh"
        self._container = None
        self._image = "alpine"
        self._name = "mtda-docker"
        self._lock = threading.Lock()
        self._proc = None

    def configure(self, conf):
        if 'command' in conf:
            self._command = conf['command']
        if 'image' in conf:
            self._image = conf['image']
        if 'name' in conf:
            self._name = conf['name']

    def probe(self):
        self.mtda.debug(3, "power.docker.probe()")

        result = None
        atexit.register(self._stop)
        self._client = docker.from_env()
        # python3-docker version <= 4.4 pulls all tags by default.
        # set tag explicitly to latest if none specified.
        image = self._image.split(":")
        distro = image[0]
        version = image[1] if len(image) > 1 else "latest"
        self._client.images.pull(distro, tag=version)
        result = self._start()

        self.mtda.debug(3, "power.docker.probe(): {}".format(result))
        return result

    def _start(self, image=None):
        self.mtda.debug(3, "power.docker._start({})".format(image))

        if image is None:
            image = self._image

        client = self._client
        result = None

        try:
            container = client.containers.get(self._name)
            if container.status == "running":
                container.stop()
            container.remove()
        except docker.errors.NotFound:
            pass

        self._container = client.containers.create(image,
                                                   stdin_open=True,
                                                   tty=True,
                                                   command=self._command,
                                                   hostname=self._name,
                                                   name=self._name)

        self.mtda.debug(3, "power.docker._start(): {}".format(result))
        return result

    def _stop(self):
        self.mtda.debug(3, "power.docker._stop()")

        result = True
        if self._container is not None:
            result = self._off()
            if result is True:
                cid = self._container.id
                try:
                    self._client.containers.get(cid)
                    self._container.remove()
                    self._container = None
                except docker.errors.NotFound:
                    self.mtda.debug(2, "power.docker._stop(): "
                                    "container {} has vanished".format(cid))
                    pass
                except docker.errors.APIError as e:
                    self.mtda.debug(1, "power.docker._stop(): "
                                    "{}".format(e))
                    result = False

        self.mtda.debug(3, "power.docker._stop(): {}".format(result))
        return result

    def command(self, args):
        return False

    def _import_close(self):
        self.mtda.debug(3, "power.docker._import_close()")

        if self._proc is None:
            raise RuntimeError("no import in progress!")

        result = False
        self._proc.communicate()
        if self._proc.returncode == 0:
            self._start(self._name)
            result = True
        self._proc = None

        self.mtda.debug(3, "power.docker._import_close(): "
                        "{}".format(result))
        return result

    def import_close(self):
        with self._lock:
            return self._import_close()

    def _import_open(self):
        self.mtda.debug(3, "power.docker._import_open()")

        if self._status() != self.POWER_OFF:
            raise RuntimeError("target isn't OFF!")

        self._stop()
        cmd = ['docker', 'import', '-', self._name]
        self._proc = subprocess.Popen(cmd,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE)
        result = self._proc.stdin

        self.mtda.debug(3, "power.docker._import_open(): "
                        "{}".format(result))
        return result

    def import_open(self):
        with self._lock:
            return self._import_open()

    def _on(self):
        self.mtda.debug(3, "power.docker._on()")

        if self._proc is not None:
            raise RuntimeError("import in progress!")

        result = True
        cid = self._container.id
        try:
            self._container.start()
            self._container = self._client.containers.get(cid)
        except docker.errors.NotFound:
            self.mtda.debug(1, "power.docker._on(): "
                            "container {} has vanished".format(cid))
            result = False
        except docker.errors.APIError as e:
            self.mtda.debug(1, "power.docker._on(): "
                            "{}".format(e))
            result = False

        self.mtda.debug(3, "power.docker._on(): {}".format(result))
        return result

    def on(self):
        with self._lock:
            return self._on()

    def _off(self):
        self.mtda.debug(3, "power.docker._off()")

        result = True
        cid = self._container.id
        try:
            self._container.stop()
            self._container = self._client.containers.get(cid)
        except docker.errors.NotFound:
            self.mtda.debug(1, "power.docker._off(): "
                            "container {} has vanished".format(cid))
            result = False
        except docker.errors.APIError as e:
            self.mtda.debug(1, "power.docker._off(): "
                            "{}".format(e))
            result = False

        self.mtda.debug(3, "power.docker._off(): {}".format(result))
        return result

    def off(self):
        with self._lock:
            return self._off()

    def _socket(self):
        self.mtda.debug(3, "power.docker._socket()")

        result = self._container.attach_socket(params={
            'logs': True,
            'stdin': True,
            'stdout': True,
            'stderr': True,
            'stream': True})

        self.mtda.debug(3, "power.docker._socket(): {}".format(result))
        return result

    def socket(self):
        with self._lock:
            return self._socket()

    def _status(self):
        self.mtda.debug(3, "power.docker._status()")

        result = self.POWER_OFF
        if self._container is not None:
            status = self._container.status
            if status == "running":
                result = self.POWER_ON
            elif status == "created" or status == "exited":
                result = self.POWER_OFF
            else:
                self.mtda.debug(1, "power.docker._status(): "
                                "unknown status: {}".format(status))

        self.mtda.debug(3, "power.docker._status(): {}".format(result))
        return result

    def status(self):
        with self._lock:
            return self._status()


def instantiate(mtda):
    return DockerPowerController(mtda)
