# ---------------------------------------------------------------------------
# USB Function network driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# System imports
from distutils.util import strtobool
import ipaddress
import os
import subprocess

# Local imports
from mtda.network.controller import NetworkController
from mtda.support.usb import Composite
from mtda.utils import System


class UsbFunctionController(NetworkController):

    def __init__(self, mtda):
        self.device = None
        self.dhcp = True
        self.dhcp_pid_file = None
        self.ipv4 = "192.168.7.1/24"
        self.mtda = mtda
        Composite.mtda = mtda

    """ Configure this network controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "network.usbf.configure()")

        if 'ipv4' in conf:
            self.ipv4 = conf['ipv4']
        if 'dhcp' in conf:
            self.dhcp = bool(strtobool(conf['dhcp']))

        result = Composite.configure('network', conf)

        self.mtda.debug(3, f"network.usbf.configure(): {result}")
        return result

    def probe(self):
        return True

    def _clean_dhcp(self):
        for f in ['conf', 'leases', 'log', 'pid']:
            attr = f'dhcp_{f}_file'
            if hasattr(self, attr):
                f = getattr(self, attr)
                if f and os.path.exists(f):
                    os.unlink(f)

    def _start_dhcp(self):
        self.dhcp_conf_file = f"/run/dnsmasq.{self.device}.conf"
        self.dhcp_leases_file = f"/run/dnsmasq.{self.device}.leases"
        self.dhcp_log_file = f"/run/dnsmasq.{self.device}.log"
        self.dhcp_pid_file = f"/run/dnsmasq.{self.device}.pid"

        self._clean_dhcp()

        cmd = ['/usr/sbin/dnsmasq', '-h']
        addr = ipaddress.IPv4Interface(self.ipv4)
        host = addr.ip + 1

        cmd.append(f'--conf-file={self.dhcp_conf_file}')

        cmd.append(f'--log-facility={self.dhcp_log_file}')
        cmd.append('--log-dhcp')

        cmd.append(f'--pid-file={self.dhcp_pid_file}')

        with open(self.dhcp_conf_file, 'w') as conf:
            conf.write(f'interface={self.device}\n')
            conf.write('bind-interfaces\n')
            conf.write(f'listen-address={addr.ip}\n')
            conf.write('dhcp-authoritative\n')
            conf.write(f'dhcp-leasefile={self.dhcp_leases_file}\n')
            conf.write(f'dhcp-host={self.host_addr},{host}\n')
            conf.write(f'dhcp-range={addr.ip},{host},{addr.netmask},12h\n')

        subprocess.check_call(cmd)

    def _stop_dhcp(self):
        if self.dhcp_pid_file and os.path.exists(self.dhcp_pid_file):
            with open(self.dhcp_pid_file, "r") as pidf:
                pid = pidf.read().strip()
                System.kill("dnsmasq", pid)

        self._clean_dhcp()
        self.dhcp_conf_file = None
        self.dhcp_leases_file = None
        self.dhcp_log_file = None
        self.dhcp_pid_file = None

    """ Bring-up the network interface"""
    def up(self):
        self.mtda.debug(3, "network.usbf.up()")

        ecm = os.path.join(Composite.path, "functions/ecm.usb0")
        ifname = os.path.join(ecm, "ifname")
        if os.path.exists(ifname) is True:
            with open(ifname) as f:
                self.device = f.read().strip()
                self.mtda.debug(2, f"network.usbf.up: device is {self.device}")
        else:
            raise RuntimeError(f'{ifname} does not exist!')

        host_addr = os.path.join(ecm, "host_addr")
        if os.path.exists(host_addr) is True:
            with open(host_addr) as f:
                self.host_addr = f.read().strip().replace('\0', '')
                self.mtda.debug(2, "network.usbf.up: "
                                   f"host_addr {self.host_addr}")
        else:
            raise RuntimeError(f'{host_addr} does not exist!')

        cmd = ["/sbin/ip", "addr", "add", self.ipv4, "dev",  self.device]
        subprocess.check_call(cmd)

        cmd = ["/sbin/ip", "link", "set", "dev", self.device, "up"]
        subprocess.check_call(cmd)

        if self.dhcp is True:
            self._start_dhcp()

        self.mtda.debug(3, "network.usbf.up: exit")

    """ Bring-down the network interface"""
    def down(self):
        self.mtda.debug(3, "network.usbf.down()")

        if self.device:
            self.mtda.debug(2, "network.usbf.down: "
                               f"bringing {self.device} down")
            if self.dhcp is True:
                self._stop_dhcp()

            cmd = ["/sbin/ip", "addr", "del", self.ipv4, "dev",  self.device]
            subprocess.check_call(cmd)

            cmd = ["/sbin/ip", "link", "set", "dev", self.device, "down"]
            subprocess.check_call(cmd)

            self.device = None
            self.host_addr = None

        self.mtda.debug(3, "network.usbf.down: exit")


def instantiate(mtda):
    return UsbFunctionController(mtda)
