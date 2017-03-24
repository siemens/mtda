#!/usr/bin/env python3

# System imports
import configparser
import importlib

# Local imports
import mtda.power.controller

class MentorTestDeviceAgent:

    def __init__(self):
        self.config_files = [ 'mtda.ini' ]
        self.power_controller = None
        self.usb_switches = []

    def target_on(self):
        if self.power_controller is not None:
            self.power_controller.on()
        else:
            print("No power controller found!")

    def target_off(self):
        if self.power_controller is not None:
            self.power_controller.off()
        else:
            print("No power controller found!")

    def usb_on(self, ndx):
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                usb_switch.on()
        except IndexError:
            print("invalid USB switch #" + str(ndx))

    def usb_off(self, ndx):
        try:
            if ndx > 0:
                usb_switch = self.usb_switches[ndx-1]
                usb_switch.off()
        except IndexError:
            print("invalid USB switch #" + str(ndx))

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
           print('power controller variant not defined!')
       except ImportError:
           print('power controller "%s" could not be found/loaded!' % (variant))
    
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
            print('usb switch variant not defined!')
        except ImportError:
            print('usb switch "%s" could not be found/loaded!' % (variant))
   
if __name__ == '__main__':
    mtda = MentorTestDeviceAgent()
    mtda.load_config()
    mtda.usb_on(1)
    mtda.target_on()

