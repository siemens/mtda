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

Lastly, the shared device may be exposed on the network using the
``storage network`` command:

    $ mtda-cli storage network

It uses `nbd-server` on the MTDA host and `sudo` and `nbd-client` on
the client (the `nbd` kernel module must loaded or built-in into the
kernel for `nbd-client to succeed). The name of the network block
device will be printed to `stdout` and should be used to detach/release
the block device when done:

    $ nbd-client -d /dev/nbd0

When using the `usbf` storage driver, a Copy-on-Write device may be
configured to receive all changes. When the storage is returned to
the host, changes may be either committed or reverted using the
`commit` or `rollback`::


    $ mtda-cli storage host
    $ mtda-cli storage commit # or rollback

Monitor commands
~~~~~~~~~~~~~~~~

When using KVM in lieu of an actual target device, arbitrary commands
may be sent to the QEMU monitor using the ``command`` command::

    $ mtda-cli command hostfwd_add tcp::8080-:8080

Keyboard
~~~~~~~~

The assist board has the capability. to act as keyboard to the DUT,general usage is
``mtda-cli keyboard write characters....`` Some special characters are supported and 
need to be enclosed between < and >

For instance: ``mtda-cli keyboard write "<down><enter>hello world<enter>"``

.. list-table:: Special Keys
   :widths: 20 80
   :header-rows: 1   
   
   * - Supported Special Keys
     - String
   * - Backspace
     - <backspace>
   * - Caps Lock
     - <capslock>
   * - Enter
     - <enter>
   * - Tab
     - <tab>
   * - Escape
     - <esc>
   * - F1
     - <f1>
   * - F2
     - <f2>
   * - F3
     - <f3>
   * - F4
     - <f4>
   * - F5
     - <f5>
   * - F6
     - <f6>
   * - F7
     - <f7>
   * - F8
     - <f8>
   * - F9
     - <f9>
   * - F10
     - <f10>
   * - F11
     - <f11>
   * - F12
     - <f12>
   * - Left
     - <left>
   * - Right
     - <right>
   * - Up
     - <up>
   * - Down
     - <down>

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

Interactive Web UI
------------------

The MTDA Web UI may be used to interact directly with the device under test if the
[video] and [www] sections are configured in the Configuration settings file.

Connections
~~~~~~~~~~

 * Connect HDMI Video Capture card to the MTDA agent's USB port.
 * Connect the other end of the capture card to the device under test display port.
 * Follow Video capture settings under the Configuration section of the document.

 .. image:: www-connections.jpg

Usage
~~~~

 * Open a browser and enter the following URL to access the MTDA Web UI
     ``http://<MTDA-AGENT-IPC>:<PORT>``

   Where <PORT> is as configured in the [www] section of the configuration settings.
   Default is 9080.
 * A web UI with MTDA control options and video stream console will be loaded as shown:

 .. image:: www-1.png

 * Hover mouse over the right panel to access the MTDA controls

 .. image:: www-3.png

 * The highlighted section in the panel is used for following actions on clicking it:

    * 1] Turn ON/OFF the device under test
    * 2] Toggle storage to host or target
    * 3] Provides option to upload image file to write to storage if connected towards host
    * 4] Opens a virtual keyboard to control the device under test
    * 5] Opens a python terminal for quick prototyping test scripts with MTDA
    * 6] Opens a window of MTDA REST API documentation
