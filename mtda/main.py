# System imports
import configparser
import daemon
import importlib
import os
import signal
import sys
import zmq

# Local imports
from   mtda.console.input import ConsoleInput
from   mtda.console.logger import ConsoleLogger
from   mtda.console.remote_output import RemoteConsoleOutput
import mtda.power.controller

class MentorTestDeviceAgent:

    def __init__(self):
        self.config_files = [ 'mtda.ini' ]
        self.console = None
        self.console_logger = None
        self.console_input = None
        self.console_output = None
        self.power_controller = None
        self.usb_switches = []
        self.ctrlport = 5556
        self.conport = 5557
        self.is_remote = False
        self.is_server = False

    def console_getkey(self):
        if self.console_input is None:
            self.console_input = ConsoleInput()
            self.console_input.start()
        return self.console_input.getkey()

    def console_head(self):
        if self.console_logger is not None:
            return self.console_logger.head()
        else:
            print("no console configured/found!", file=sys.stderr)
            return None

    def console_lines(self):
        if self.console_logger is not None:
            return self.console_logger.lines()
        else:
            print("no console configured/found!", file=sys.stderr)
            return None

    def console_remote(self, host):
        if self.is_remote == True:
            # Create and start our remote console
            self.console_output = RemoteConsoleOutput(host, self.conport)
            self.console_output.start()

    def console_send(self, data):
        if self.console_logger is not None:
            return self.console_logger.write(data)
        else:
            print("no console configured/found!", file=sys.stderr)
            return None

    def toggle_timestamps(self):
        if self.console_logger is not None:
            return self.console_logger.toggle_timestamps()
        else:
            print("no console configured/found!", file=sys.stderr)
            return None

    def target_on(self):
        if self.power_controller is not None:
            self.power_controller.on()
        else:
            print("no power controller found!", file=sys.stderr)

    def target_off(self):
        if self.power_controller is not None:
            self.power_controller.off()
            if self.console_logger is not None:
                return self.console_logger.reset_timer()
        else:
            print("no power controller found!", file=sys.stderr)

    def target_toggle(self):
        if self.power_controller is not None:
            status = self.power_controller.toggle()
            if status == self.power_controller.POWERED_OFF and self.console_logger is not None:
                return self.console_logger.reset_timer()
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

    def usb_toggle(self, ndx):
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                usb_switch.toggle()
        except IndexError:
            print("invalid USB switch #" + str(ndx), file=sys.stderr)

    def load_config(self, is_remote=False, is_server=False):
        self.is_remote = is_remote
        self.is_server = is_server
        parser = configparser.ConfigParser()
        configs_found = parser.read(self.config_files)
        if is_remote == False:
            if parser.has_section('console'):
                self.load_console_config(parser)
            if parser.has_section('power'):
                self.load_power_config(parser)
            if parser.has_section('usb'):
                self.load_usb_config(parser)

    def load_console_config(self, parser):
        try:
            # Get variant
            variant = parser.get('console', 'variant')
            # Try loading its support class
            mod = importlib.import_module("mtda.console." + variant)
            factory = getattr(mod, 'instantiate')
            self.console = factory()
            # Configure the console
            self.console.configure(dict(parser.items('console')))
        except configparser.NoOptionError:
            print('console variant not defined!', file=sys.stderr)
        except ImportError:
            print('console "%s" could not be found/loaded!' % (variant), file=sys.stderr)
    
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

    def start(self):
        if self.is_remote == True:
            return None

        if self.console is not None:
            # Create a publisher
            if self.is_server == True:
                context = zmq.Context()
                socket = context.socket(zmq.PUB)
                socket.bind("tcp://*:%s" % self.conport)
            else:
                socket = None

            # Create and start console logger
            self.console.probe()
            self.console_logger = ConsoleLogger(self.console, socket)
            self.console_logger.start()

