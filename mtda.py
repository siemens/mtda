#!/usr/bin/env python3

# System imports
import configparser
import daemon
import getopt
import importlib
import lockfile
import os
import signal
import sys
import zerorpc

# Local imports
import mtda.power.controller
from mtda.server import Server

class MultiTenantDeviceAccess:

    def __init__(self):
        self.config_files = [ 'mtda.ini' ]
        self.power_controller = None
        self.usb_switches = []
        self.pidfile = "/var/run/mtda.pid"
        self.logfile = "/var/log/mtda.log"
        self.ctrlport = 5556
        self.remote = None

    def daemonize(self):
        print("starting daemon")
        context = daemon.DaemonContext(
            working_directory=os.getcwd(),
            stdout=open(self.logfile, 'w+'),
            stderr=open(self.logfile, 'w+'),
            umask=0o002,
            pidfile=lockfile.FileLock(self.pidfile)
        )

        context.signal_map = {
            signal.SIGTERM: 'terminate',
            signal.SIGHUP:  'terminate',
        }

        with context:
            self.server()

    def server(self):
        srv = Server(self)
        srv.run("tcp://*:%d" % self.ctrlport)

    def client(self):
        uri = "tcp://%s:%d" % (self.remote, self.ctrlport)

        c = zerorpc.Client()
        c.connect(uri)
        return c

    def target_on(self):
        if self.remote is not None:
            c = self.client()
            c.target_on()
        else:
            if self.power_controller is not None:
                self.power_controller.on()
            else:
                print("no power controller found!", file=sys.stderr)

    def target_off(self):
        if self.remote is not None:
            c = self.client()
            c.target_off()
        else:
            if self.power_controller is not None:
                self.power_controller.off()
            else:
                print("no power controller found!", file=sys.stderr)

    def usb_on(self, ndx):
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                usb_switch.on()
        except IndexError:
            print("invalid USB switch #" + str(ndx), file=sys.stderr)

    def usb_off(self, ndx):
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                usb_switch.off()
        except IndexError:
            print("invalid USB switch #" + str(ndx), file=sys.stderr)

    def load_config(self):
        parser = configparser.ConfigParser()
        configs_found = parser.read(self.config_files)
        if parser.has_section('power'):
            self.load_power_config(parser)
        if parser.has_section('usb'):
            self.load_usb_config(parser)
    
    def load_power_config(self, parser):
       try:
           # Get variant
           variant = parser.get('power', 'variant')
           # Try loading its support class
           mod = importlib.import_module("mtda.power." + variant)
           factory = getattr(mod, 'instantiate')
           self.power_controller = factory()
           # Configure and probe the power controller
           self.power_controller.configure(dict(parser.items('power')))
           self.power_controller.probe()
       except configparser.NoOptionError:
           print('power controller variant not defined!', file=sys.stderr)
       except ImportError:
           print('power controller "%s" could not be found/loaded!' % (variant), file=sys.stderr)
    
    def load_usb_config(self, parser):
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
        try:
            # Get variant
            variant = parser.get(section, 'variant')
            # Try loading its support class
            mod = importlib.import_module("mtda.usb." + variant)
            factory = getattr(mod, 'instantiate')
            usb_switch = factory()
            # Configure and probe the USB switch
            usb_switch.configure(dict(parser.items(section)))
            usb_switch.probe()
            self.usb_switches.append(usb_switch)
        except configparser.NoOptionError:
            print('usb switch variant not defined!', file=sys.stderr)
        except ImportError:
            print('usb switch "%s" could not be found/loaded!' % (variant), file=sys.stderr)

    def target_cmd(self, args):
        if len(args) > 0:
            cmd = args[0]
            args.pop(0)
            if cmd == "off":
                self.target_off()
            elif cmd == "on":
                self.target_on()
            else:
                print("unknown target command '%s'!" %(cmd), file=sys.stderr)

    def main(self):
        daemonize = False
        detach = True

        options, stuff = getopt.getopt(sys.argv[1:], 
            'dnr:',
            ['daemon', 'no-detach', 'remote='])
        for opt, arg in options:
            if opt in ('-d', '--daemon'):
                daemonize = True
            if opt in ('-n', '--no-detach'):
                detach = False 
            if opt in ('-r', '--remote'):
                self.remote = arg

        # Load default/specified configuration
        self.load_config()

        # Start our server
        if daemonize == True:
            if detach == True:
                self.daemonize()
            else:
                self.server()

        # Check for non-option arguments
        if len(stuff) > 0:
           cmd = stuff[0]
           stuff.pop(0)

           cmds = {
              'target' : self.target_cmd
           } 

           if cmd in cmds:
               cmds[cmd](stuff)
           else:
               print("unknown command '%s'!" %(cmd), file=sys.stderr)
               sys.exit(1)

if __name__ == '__main__':
    mtda = MultiTenantDeviceAccess()
    mtda.main()

