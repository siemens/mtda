Build Your Own
==============

This chapter describes how you may build your own device to run the agent
side of MTDA. Most of the configurations presented here are basic and may
be enhanced with additional electronic gadgets.

NanoPI NEO-LTS
--------------

The NanoPi NEO (abbreviated as NEO) is another fun board developed by
FriendlyARM for makers, hobbyists and fans.

It is powered by an Allwinner H3 (Cortex A7), has a microSD slot, a microUSB
OTG port, a USB-Host Type A port, an Ethernet port and GPIO pins.

Debian (buster) will be loaded on the microSD card and will include the MTDA
agent. It will communicate with its clients over Ethernet. An electric relay
will be controlled via a GPIO line in order to drive power for our Device Under
Test. Communication with that device will be achieved via the USB OTG port
where the following functions will be exposed:

 * ACM: provide a Serial over USB port. The Operating System running on the
   Device Under Test may use this virtual serial port to provide a login
   shell to MTDA clients.

 * HID: the NanoPI NEO-LTS will be seen as a keyboard. This may be used by e.g.
   ``power on`` scripts to enter the firmware of the Device Under Test to
   select a boot media (SSD or USB).

 * Mass Storage: a USB stick will be connected to the USB Host available on the
   NanoPI NEO-LTS and will be exposed to the Device Under Test. MTDA will allow
   clients to write a new OS image for the device it is connected to.

Building the microSD card image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``kas-docker`` to build a Debian image for the nanoPI NEO-LTS with MTDA
pre-installed::

    $ kas-docker --isar build kas/mtda-nanopi-neo.yml

Insert a microSD card to your system and write the generated image::

    # Check the microSD card device, /dev/mmcblk0 is used as an example
    $ sudo dd if=build/tmp/deploy/images/nanopi-neo/isar-*.wic.img \
      of=/dev/mmcblk0 bs=8M

Booting the NanoPI NEO-LTS
~~~~~~~~~~~~~~~~~~~~~~~~~~

Insert the microSD card created above into the microSD card slot of your NanoPI
NEO-LTS and connect the board to your network. Attach a formatted USB stick to
the USB-Host port. Lastly, get a microUSB cable, connect your system and the
NEO together. The red LED of the NEO should light up as well as the LEDs from
the RJ45 port. Your system should detect a mass storage after the NEO has
booted. A new serial port and keyboard should also be detected. You may also
check that your NEO has obtained an IP address. Use ``ssh`` to connect (use
``mtda`` as both login and password).

Attaching an electric relay
~~~~~~~~~~~~~~~~~~~~~~~~~~~

We will use a 5V relay such as the JQC3F-05VDC pictured below:

.. image:: jqc3f-05vdc.jpg

It requires a 5V line, ground and signal. Here is the pin-out of our NanoPI
NEO-LTS:

.. image:: neo_pinout.jpg

We will use pin #4 (``5V OUT``) to deliver 5V to the relay, pin #6 (``GND``) to
connect the relay to ground and pin #7 (``PG11``) to drive the relay. It should
be noted that the signal GPIO pin is seen as GPIO ``203`` in Linux.

Configuring MTDA
~~~~~~~~~~~~~~~~

A configuration file should be created on the NanoPI NEO-LTS. Use ``ssh`` to
connect with the ``mtda`` user and then ``sudo`` to get elevated privileges::

    $ ssh mtda@172.17.0.2
    The authenticity of host '172.17.0.2 (172.17.0.2)' can't be established.
    ECDSA key fingerprint is SHA256:X4hTqfSmfG1bet2Bg/MfU1fNMgp30T+6SkAwLXZbJTQ.
    Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
    Warning: Permanently added '172.17.0.2' (ECDSA) to the list of known hosts.
    mtda@172.17.0.2's password: mtda 
    Linux mtda 4.19.0-11-armmp #1 SMP Debian 4.19.146-1 (2020-09-17) armv7l

    The programs included with the Debian GNU/Linux system are free software;
    the exact distribution terms for each program are described in the
    individual files in /usr/share/doc/*/copyright.

    Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
    permitted by applicable law.
    Last login: Sun Sep 27 18:40:42 2020 from 172.17.0.100
    $ sudo -s
    [sudo] password for mtda: mtda
    #

Use ``vi`` to create an initial configuration::

    # vi /etc/mtda/config

Hit ``i`` to enter the input mode and type the following configuration::

    [console]
    variant=serial
    port=/dev/ttyGS0
    rate=9600

    [power]
    variant=gpio
    pin=203

    [keyboard]
    variant=hid
    device=/dev/hidg0

    [sdmux]
    variant=usbf

Hit ``ESC`` to leave the input mode and type ``:x`` to exit. You should be back
to the shell and may restart the agent::

    # sync
    # systemctl restart mtda

Clients may now connect to the MTDA agent, control the power input of the Device
Under Test and remotely access its console.
