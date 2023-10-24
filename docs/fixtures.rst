Test fixtures
=============

Multi-function test fixtures
----------------------------

USB Function
~~~~~~~~~~~~

When the MTDA agent is running on devices such as the NanoPi NEO, it may
provide the following USB functions to the DUT:

 * USB Mass Storage
 * USB HID (Keyboard)
 * USB ACM

Its vendor/product ID pair is ``1d6b:0104`` and its serial number of the form
``mtda-`` followed by alphanumeric characters (``2020`` at this time but will
eventually become a unique identifier).

The USB Mass Storage function may be used as a shared storage between the agent
and the DUT. This capability is particularly useful with systems that may boot
from a USB Mass Storage device. For PCs, this often requires entering the boot
menu and selecting USB as boot media.

The USB HID (Keyboard) was added when early interaction with the DUT is needed.
This may be used in a ``power on`` script like the following::

    [scripts]
    power on:
        import time
        time.sleep(5)
        mtda.keyboard.esc(5)
        time.sleep(0.5)
        mtda.keyboard.down()
        mtda.keyboard.enter()
        mtda.keyboard.idle()

Key events are sent blindly. When the Operating System comes up on the DUT, it
may detect the USB ACM function and open a serial console (such as ``agetty``)
to provide a MTDA console to clients. On the agent side, the serial device will
usually be ``/dev/ttyGS0`` and should be configured with a speed of ``9600``
bauds.

The following blocks may be added to the MTDA configuration file used by the
agent to enable the functions listed above::

    [console]
    variant=usbf

    [storage]
    variant=usbf
    file=/dev/sda

    [keyboard]
    variant=hid
    device=/dev/hidg0
