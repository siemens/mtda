Usage
=====

Command line
------------

The MTDA client may be used from the command line using the ``mtda-cli``
command. A remote agent may be specified on the command line using the
``-r`` option or in the environment with the ``MTDA_REMOTE`` variable.
The remote may be alternatively specified in the ``[remote]]`` section
of the local configuration file.

Power commands 
~~~~~~~~~~~~~~

When MTDA is configured with a ``[power]`` control block in its configuration,
the ``target`` command may be used to power the attached target device ON or
OFF::

    # Turn the target on
    $ mtda-cli target on

    # Use the target...

    # Turn the target off
    $ mtda-cli target off

Both commands will fail and return a non-zero status when no power controller
is attached.

Use the ``reset`` command to power-cycle the device::

    $ mtda-cli target reset

Uptime may be printed with the ``uptime`` command::

    $ mtda-cli target uptime
    16 minutes 33 seconds

This is the elapsed time since the device was powered and does not account for
soft resets triggered from the Operating System or hardware watchdog.

Console commands
~~~~~~~~~~~~~~~~

Most MTDA setups will have a console setup to communicate with the target
device. In most cases, this console is simply a serial console either via
RS232 or via USB. Commands (such as boot-loader commands or shell commands)
may be sent using ``console send``::

    $ mtda-cli console send "run boot_usb\n"

You may then check how many lines are in the console buffer::

    $ mtda-cli console lines
    14

You may extract the first line from the ring buffer with the ``console head``
command::

    $ mtda-cli console head
    U-Boot 2015.07 (Jan 08 2017 - 16:25:06 +0100)

or get everything queued in the buffer with ``console flush``::

    $ mtda-cli console flush
    U-Boot 2015.07 (Jan 08 2017 - 16:25:06 +0100)
    ...
    U-Boot>

Data in the ring buffer may also be discarded with ``console clear``::

    $ mtda-cli console clear

Wait up to 60 seconds for a given string on the console::

    $ mtda-cli console wait "login:" 60

Monitor commands
~~~~~~~~~~~~~~~~

Some devices may have a secondary console that may be used to control the
system. Data received from the monitor interface is logged into a ring
buffer that may be read with the ``monitor`` commands listed below.

Send a command (string) to the monitor interface::

    $ mtda-cli monitor send "run boot_usb\n"

Wait up to 30 seconds for a given string on the monitor console::

    $ mtda-cli monitor wait "Hit any key" 30

Storage commands
~~~~~~~~~~~~~~~~

A shared storage device may be controlled with the ``storage`` command in
supported setups (e.g. using special hardware such as the SDMux or when
sharing a media attached to the MTDA host using USB Function). In most
configurations, the target device should be OFF when swapping the shared
device between the ``HOST`` (i.e. the system running the MTDA daemon) and
the ``TARGET`` device. To attach the shared storage to the host, use::

    $ mtda-cli storage host

It is then possible to "burn" disk images using the ``storage write``
command::

    $ mtda-cli storage write console-image.wic.bz2

Images may also be downloaded from a S3 bucket::

    $ export AWS_ACCESS_KEY_ID=my-access-key
    $ export AWS_SECRET_ACCESS_KEY=my-secret-access-key
    $ mtda-cli storage write s3://example.org/console-image.wic.zst

It should be noted that MTDA supports ``.gz``, ``.bz2``, ``.zst`` and
raw images.

Partitions may be mounted on the MTDA host using the ``storage mount``
command::

    $ mtda-cli storage mount 1 # mount 1st partition

The client may then send files to be updated on the mounted partition with
the ``storage update`` command::

    # Update the kernel image
    # (here boot/kernel on the mounted partition, vmlinuz on the client)
    $ mtda-cli storage update boot/kernel vmlinuz

The shared device may be swapped to the ``TARGET`` device the ``storage
target`` command::

    $ mtda-cli storage target

Monitor commands
~~~~~~~~~~~~~~~~

When using KVM in lieu of an actual target device, arbitrary commands
may be sent to the QEMU monitor using the ``command`` command::

    $ mtda-cli command hostfwd_add tcp::8080-:8080

Interactive
-----------

The MTDA client may be used as a terminal to interact directly with the
device under test.

Usage
~~~~~

Start ``mtda-cli`` without any commands. You may use a custom remote agent
using the ``-r`` (or `--remote``) option::

    # use default remote (localhost or remote specified in the configuration)
    $ mtda-cli

    # or with a specific remote
    $ mtda-cli -r mtda-for-pi3.local

Key bindings
~~~~~~~~~~~~

The following key bindings may be used to control MTDA from the interactive console:

 * ``Ctrl-a`` + ``a``: acquire the target
 * ``Ctrl-a`` + ``b``: paste console buffer to pastebin.com
 * ``Ctrl-a`` + ``c``: start/stop screen capture to "screen.cast"
 * ``Ctrl-a`` + ``i``: print target information (power status, SD card, USB ports, etc.)
 * ``Ctrl-a`` + ``m``: switch between the monitor and the console
 * ``Ctrl-a`` + ``p``: toggle power on/off
 * ``Ctrl-a`` + ``q``: quit
 * ``Ctrl-a`` + ``r``: release the target
 * ``Ctrl-a`` + ``s``: swap the shared storage device between the host and target
 * ``Ctrl-a`` + ``t``: toggle display of timestamps
 * ``Ctrl-a`` + ``u``: toggle the 1st USB port on/off
