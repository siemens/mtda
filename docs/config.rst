Configuration
=============

MTDA will reads it configuration from:

 * $HOME/.mdta/config
 * /etc/mtda/config

Configuration files are similar to what’s found in Microsoft Windows INI
files (Python's `configparser` module is used to parse them).

It is possible to override some settings using environment variables.

Configuration reference
~~~~~~~~~~~~~~~~~~~~~~~

* ``main``: [optional]
    Usually placed at the top of MTDA configuration files. It contains general
    settings.

  * ``debug``: integer [optional]
      Level of debug messages to print out while running (set to 0 to turn all
      debug messages off).

  * ``fuse``: boolean [optional]
      Enable support for mounting partitions from the shared device using FUSE
      instead of ``losetup`` and ``mount``. This feature is experimental and
      requires ``partitionfs``, ``fuseext2`` and ``fusefat``.
