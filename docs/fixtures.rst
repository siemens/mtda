Test fixtures
=============

Multi-function test fixtures
----------------------------

USB Function
~~~~~~~~~~~~

When the MTDA agent is running on devices such as the NanoPI NEO, it may
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
    variant=serial
    port=/dev/ttyGS0
    rate=9600

    [storage]
    variant=usbf
    device=/dev/sda

    [keyboard]
    variant=hid
    device=/dev/hidg0

If the ``storage`` function was enabled, ``/etc/mtda/usb-functions`` should
be created and also specify the block device to be used::

    MASS_STORAGE_FILE=/dev/sda

Since the ``mtda-usb-functions`` service should only be started after the
specified device was detected, a dependency should be added to the service
using a systemd drop-in unit::

    mkdir /lib/systemd/system/mtda-usb-functions.service.d
    printf "[Unit]\nAfter=dev-sda.device" \
        > /lib/systemd/system/mtda-usb-functions.service.d/10-wait-dev.conf

The system should be restarted. Use ``systemctl status mtda-usb-functions`` to
confirm that the service was correctly started.
