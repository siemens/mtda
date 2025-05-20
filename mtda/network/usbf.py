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
        self.forward_rules = None
        self.ipv4 = "192.168.7.1/24"
        self.peer = None
        self.mtda = mtda
        Composite.mtda = mtda

    """ Configure this network controller from the provided configuration"""
    def configure(self, conf):
        self.mtda.debug(3, "network.usbf.configure()")

        if 'ipv4' in conf:
            self.ipv4 = conf['ipv4']
        if 'dhcp' in conf:
            self.dhcp = bool(strtobool(conf['dhcp']))
        if 'forward' in conf:
            self.forward_rules = self._parse_forward(conf['forward'])
        if 'peer' in conf:
            self.peer = ipaddress.IPv4Address(conf['peer'])

        addr = ipaddress.IPv4Interface(self.ipv4)
        if self.peer is None:
            self.peer = addr.ip + 1
        self.mtda.debug(2, f'agent at {addr.ip}')
        self.mtda.debug(2, f'device (peer) at {self.peer}')

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
            conf.write(f'dhcp-host={self.host_addr},{self.peer}\n')
            conf.write(f'dhcp-range={addr.ip},{self.peer},'
                       f'{addr.netmask},12h\n')

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

    def _parse_forward(self, expr):
        rules = []
        for rule in expr.split(','):
            parts = rule.strip().split(':')
            if len(parts) != 3:
                raise ValueError(f"Invalid rule format: '{rule}' "
                                 "(expected proto:local-port:remote-port)")

            proto, local_str, remote_str = parts
            if proto not in ("tcp", "udp"):
                raise ValueError(f"Unsupported protocol '{proto}' "
                                 "in rule '{rule}'")

            try:
                local = int(local_str)
                remote = int(remote_str)
            except ValueError:
                raise ValueError(f"Ports must be integers in rule '{rule}'")

            for port, label in [(local, "local"), (remote, "remote")]:
                if not (1 <= port <= 65535):
                    raise ValueError(f"{label.capitalize()} "
                                     "port out of range in rule '{rule}'")

            rules.append((proto, local, remote))
        return rules

    def _apply_forward_rules(self):
        for rule in self.forward_rules:
            proto, local, remote = rule

            cmd = ['/sbin/iptables', '-t', 'nat', '-A', 'PREROUTING', '-p',
                   proto, '--dport', str(local), '-j', 'DNAT',
                   '--to-destination', f'{self.peer}:{remote}']
            subprocess.check_call(cmd)

            cmd = ['/sbin/iptables', '-t', 'nat', '-A', 'POSTROUTING', '-p',
                   proto, '-d', str(self.peer), '--dport', str(remote), '-j',
                   'MASQUERADE']
            subprocess.check_call(cmd)

    def _remove_forward_rules(self):
        for rule in self.forward_rules:
            proto, local, remote = rule

            cmd = ['/sbin/iptables', '-t', 'nat', '-D', 'PREROUTING', '-p',
                   proto, '--dport', str(local), '-j', 'DNAT',
                   '--to-destination', f'{self.peer}:{remote}']
            subprocess.check_call(cmd)

            cmd = ['/sbin/iptables', '-t', 'nat', '-D', 'POSTROUTING', '-p',
                   proto, '-d', str(self.peer), '--dport', str(remote), '-j',
                   'MASQUERADE']
            subprocess.check_call(cmd)

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

        self.mtda.debug(2, f"dhcp for {self.device}? {self.dhcp}")
        if self.dhcp is True:
            self._start_dhcp()

        self.mtda.debug(2, f"forward rules for {self.device}? "
                           f"{self.forward_rules is not None}")
        if self.forward_rules:
            self._apply_forward_rules()

        self.mtda.debug(3, "network.usbf.up: exit")

    """ Bring-down the network interface"""
    def down(self):
        self.mtda.debug(3, "network.usbf.down()")

        if self.device:
            self.mtda.debug(2, "network.usbf.down: "
                               f"bringing {self.device} down")

            if self.forward_rules:
                self._remove_forward_rules()
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
