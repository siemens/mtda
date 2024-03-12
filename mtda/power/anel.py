# ---------------------------------------------------------------------------
# Anel power strip driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (c) Siemens AG, 2024
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
import socket
from contextlib import contextmanager

# Local imports
from mtda.power.controller import PowerController


class AnelPowerController(PowerController):

    def __init__(self, mtda):
        self._host = None
        self._plug = None
        self._user = "admin"
        self._password = "anel"
        self._port_in = 77
        self._port_out = 75
        self._status = self.POWER_OFF
        self.mtda = mtda

    def configure(self, conf):
        if 'host' in conf:
            self._host = conf['host']
        if 'plug' in conf:
            self._plug = int(conf['plug'])
        if 'user' in conf:
            self._user = conf['user']
        if 'password' in conf:
            self.password = conf['password']
        if 'port_in' in conf:
            self.check_on = int(conf['port_in'])
        if 'port_out' in conf:
            self.check_on = int(conf['port_out'])

    def probe(self):
        if self._host is None:
            raise ValueError("host not specified")
        if self._plug is None:
            raise ValueError("plug not specified")

    def command(self, args):
        return False

    @contextmanager
    def _in(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self._port_in))
        sock.settimeout(0.5)
        yield sock
        sock.close()

    @contextmanager
    def _out(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        yield sock
        sock.close()

    def _send(self, payload):
        data = (payload + self._user + self._password).encode('latin')
        with self._out() as connection:
            connection.sendto(data, (self._host, self._port_out))

    def _receive(self):
        with self._in() as connection:
            data, _ = connection.recvfrom(1024)
        return data.decode('latin')

    def _switch(self, state):
        payload = f"Sw_{'on' if state else 'off'}{self._plug}"
        self._send(payload)

        try:
            result = self._receive().split(':')[5+self._plug].rsplit(',', 1)[1]
        except TimeoutError:
            self.mtda.debug(3, "power.anel._switch(): TimeoutError")

        if result == "0":
            self._status = self.POWER_OFF
        elif result == "1":
            self._status = self.POWER_ON
        else:
            self._status = self.POWER_UNSURE

    def on(self):
        self._switch(True)
        return self._status == self.POWER_ON

    def off(self):
        self._switch(False)
        return self._status == self.POWER_OFF

    def status(self):
        return self._status

    def toggle(self):
        if self.status() == self.POWER_OFF:
            self.on()
        else:
            self.off()
        return self.status()


def instantiate(mtda):
    return AnelPowerController(mtda)
