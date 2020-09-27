Configuration
=============

MTDA will reads it configuration from:

 * $HOME/.mdta/config
 * /etc/mtda/config

Configuration files are similar to what’s found in Microsoft Windows INI
files (Python's `configparser` module is used to parse them).

It is possible to override some settings using environment variables.

General settings
~~~~~~~~~~~~~~~~

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
