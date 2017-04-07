
# Overview

Mentor Test Device Agent (or MTDA for short) is a relatively small Python application
acting as an interface to a test device. It provides mechasnims to remotely turn the
device on or off (assuming an IP/USB power switch is available), plug USB devices in
or out (also requiring special hardware) or simply access its console (in most cases
serial).

# Configurations

## Base

In its most basic configuration, MTDA may be used with:

   * a computer running Ubuntu
   * a target device
   * a serial connection between the two

In this configuration, power and USB control functions will not be available.

## Pi3 + Power/USB switches

A relatively cheap configuration may look like this:

   * a Raspberry Pi3 connected to your Wi-Fi network and running mtda as a daemon
   * a target device
   * a serial connection between the two
   * an Aviosys 8800 power switch (connected via USB to the Pi3)
   * a home-made USB switch (connected via GPIO to the Pi3)

In this configuration, the target device may be used from computers running mtda as
a client and connecting to the remote agent.
 
# Installation

For hosts running Ubuntu 16.04 (or later), the following packages need to be installed:

```
sudo apt-get install \
   python3-daemon python3-dev python3-serial \
   python3-setuptools python3-usb python3-zmq
```

# Configuring MTDA

The agent reads its configuration from mtda.ini.
Check the sample configuration file included with this distribution for supported options.

# Starting the daemon

The MTDA daemon may be started as follows:

```
$ sudo python3 mtda.py -d
```

# Client commands

Here are a few commands supported by mtda:

```
# Turn the target on
$ python3 mtda.py -r 192.168.0.104 target on

# Send the "run boot_usb" command to the boot-loader
$ python3 mtda.py -r 192.168.0.104 console send "run boot_usb\n"

# Get the first line from the console buffer
$ python3 mtda.py -r 192.168.0.104 console head

# Interact with the console
$ python3 mtda.py -r 192.168.0.104
# The interactive console may alse be invoked as follows:
$ python3 mtda.py -r 192.168.0.104 console interactive

# Power off the target
$ python3 mtda.py -r 192.168.0.104 target off
```

# Interactive console

The 'console interactive' command allows remote interaction with the device console.
The following key sequences may be used to control MTDA:

   * Ctrl + a + p: toggle power on/off
   * Ctrl + a + q: quit
   * Ctrl + a + t: toggle display of timestamps
   * Ctrl + a + u: toggle the 1st USB port on/off

