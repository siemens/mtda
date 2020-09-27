Configuration
=============

MTDA will reads it configuration from:

 * $HOME/.mdta/config
 * /etc/mtda/config

Configuration files are similar to what’s found in Microsoft Windows INI
files (Python's `configparser` module is used to parse them).

It is possible to override some settings using environment variables.

General settings
----------------

* ``main``: section [optional]
    Usually placed at the top of MTDA configuration files. It contains general
    settings.

  * ``debug``: integer [optional]
      Level of debug messages to print out while running (set to 0 to turn all
      debug messages off).

  * ``fuse``: boolean [optional]
      Enable support for mounting partitions from the shared device using FUSE
      instead of ``losetup`` and ``mount``. This feature is experimental and
      requires ``partitionfs``, ``fuseext2`` and ``fusefat``.

* ``console``: section [optional]
    Specify console settings when running the agent-side of MTDA (this section
    is ignored when running MTDA as a client). The ``variant`` key should be
    set, other settings in this section are variant-specific.

  * ``variant``: string [required]
      Select a console variant. MTDA provides the following drivers: ``serial``
      and ``telnet``.

* ``keyboard``: section [optional]
    Specify a keyboard driver.

  * ``variant``: string [required]
      Select a keyboard driver between ``hid`` and ``qemu``.

* ``power``: section [optional]
    Configure a power controller for the device attached to MTDA. The driver
    may be selected with ``variant``.

  * ``variant``: string [required]
      Select a power variant from ``aviosys_8800``, ``gpio``, ``pduclient`` and
      ``qemu``.

* ``remote``: section [optional]
    Specify the host and ports to connect to when using a MTDA client (such as
    ``mtda-cli``).

  * ``control``: integer [optional]
      Remote port listening for control commands (defaults to ``5556``).

  * ``console``: integer [optional]
      Remote port to connect to in order to get console messages (defaults to
      ``5557``).

  * ``host``: string [optional]
      Remote host name or ip to connect to as a client to interact with the
      MTDA agent (defaults to ``localhost``).

* ``scripts``: section [optional]
    Python scripts to be executed upon certain events. Use ``... `` instead of
    hard/soft spaces.

  * ``power off``: string [optional]
      Execute a Python script when the device is powered off.
     
  * ``power on``: string [optional]
      Execute a Python script when the device is powered on.
     
* ``sdmux``: section [optional]
    Configure a shared storage driver that may be swapped between the device
    attached to MTDA and the host running the agent. The driver will be
    selected with ``variant``.

  * ``variant``: string [required]
      Select a sdmux variant from ``qemu``, ``samsung`` and ``usbf``.

* ``usb``: section [optional]
    Specify how many USB ports may be controlled from this agent.

  * ``ports``: integer [optional]
      Number of USB ports. Each port should then be configured with its own
      ``[usbN]`` section where ``N`` is the port index (starting from ``1``).

Power settings
--------------

The ``[power]`` section configures a power controller to power the device on or
off. The driver is selected with the ``variant`` setting. Driver-specific
settings are detailed below.

``aviosys_8800`` driver settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``aviosys_8800`` driver supports the USB controller power outlet from
Aviosys. The following settings are supported:

* ``pid``: integer [optional]
    The USB product ID of the power outlet (defaults to ``2303``).

* ``vid``: integer [optional]
    The USB vendor ID of the power outlet (defaults to ``067b``).

``gpio`` driver settings
~~~~~~~~~~~~~~~~~~~~~~~~

The ``gpio`` driver may be used to control a simple electric relay using GPIO
lines from the system running the MTDA agent. The following settings are
supported:

* ``pin``: integer [required]
    Specify the GPIO pin number to be used to control the relay.

``pduclient`` driver settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``pduclient`` driver may be used to let a LAVA instance control the power
of the device attached to MTDA. The following settings are supported:

* ``daemon``: string [required]
    Determines the hostname of the hostname which is running ``lavapdu-listen``
    to which the MTDA agent can connect to and send power commands.

* ``hostname``: string [required]
    The PDU which will run power commands sent by the MTDA agent.

* ``port``: integer [required]
    The port on the specified PDU to which the device is connected.

``qemu`` driver settings
~~~~~~~~~~~~~~~~~~~~~~~~

The ``qemu`` driver may be used to use QEMU/KVM instead of a physical device.
The following settings are supported:

* ``bios``: string [optional]
    The BIOS to be loaded by QEMU/KVM.

* ``cpu``: string [optional]
    The CPU to be emulated by QEMU/KVM.

* ``executable``: string [optional]
    The QEMU/KVM executable to use as system emulator. This setting defaults
    to ``kvm``

* ``hostname``: string [optional]
    Name of emulated machine to be provided by QEMU/KVM internal DHCP server.

* ``machine``: string [optional]
    The QEMU/KVM machine to emulate.

* ``memory``: integer [optional]
    The amount of memory (in mega-bytes) for the emulated machime (defaults to
    512 MiB).

* ``pflash_ro``: string [optional]
    Path to the read-only firmware flash.

* ``pflash_rw``: string [optional]
    Path to the read-write firmware flash.

* ``storage``: string [optional]
    Path to the emulated machine storage.

* ``swtpm``: string [optional]
    Path to the ``swtpm`` binary to support emulation of a TPM device.

* ``watchdog``: string [optional]
    Name of the watchdog driver provided by QEMU/KVM for the selected machine.
