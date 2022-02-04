Set Static IP Address Using nmcli Tool
======================================

Using nmcli tool, you can modify a network interface to use a static IP address.

Commands to be executed
~~~~~~~~~~~~~~~~~~~~~~~
Use the ``con show`` command to  check the active ``connection name``::

    $ nmcli con show
    NAME                UUID                                  TYPE      DEVICE
    Wired connection 1  3a225b30-3f00-3223-9462-3096e837ab88  ethernet  eth0


First, run the command below to set up the IP address ::

    $ sudo nmcli con mod 'Wired connection 1' ipv4.addresses 134.86.61.26/25

Should be noted CIDR ``/25`` is for netmask ``255.255.255.128`` and ``/24``, ``/16``
are for ``255.255.255.0``, ``255.255.0.0`` respectively.

Next configure the default gateway as shown::

    $ sudo nmcli con mod 'Wired connection 1' ipv4.gateway 134.86.61.126

Then set up the DNS server::

    $ sudo nmcli con mod 'Wired connection 1' ipv4.dns 137.202.187.16

change the addressing from DHCP to static::

    $ sudo nmcli con mod 'Wired connection 1' ipv4.method manual

Settings for the updated configuration may be checked with ``nmcli device show`` as shown below::

    # Show the comple
    $ nmcli device show
    GENERAL.DEVICE:                         eth0
    GENERAL.TYPE:                           ethernet
    GENERAL.HWADDR:                         9E:55:11:EF:14:42
    GENERAL.MTU:                            1500
    GENERAL.STATE:                          100 (connected)
    GENERAL.CONNECTION:                     Wired connection 1
    GENERAL.CON-PATH:                       /org/freedesktop/NetworkManager/ActiveConnection/1
    WIRED-PROPERTIES.CARRIER:               on
    IP4.ADDRESS[1]:                         134.86.61.26/25
    IP4.GATEWAY:                            134.86.61.126
    IP4.ROUTE[1]:                           dst = 134.86.61.0/25, nh = 0.0.0.0, mt = 100
    IP4.ROUTE[2]:                           dst = 0.0.0.0/0, nh = 134.86.61.126, mt = 100
    IP4.DNS[1]:                             137.202.187.16
    IP6.ADDRESS[1]:                         fe80::6aa:4676:4cf4:3760/64
    IP6.GATEWAY:                            --
    IP6.ROUTE[1]:                           dst = fe80::/64, nh = ::, mt = 100
    IP6.ROUTE[2]:                           dst = ff00::/8, nh = ::, mt = 256, table=255

    GENERAL.DEVICE:                         lo
    GENERAL.TYPE:                           loopback
    GENERAL.HWADDR:                         00:00:00:00:00:00
    GENERAL.MTU:                            65536
    GENERAL.STATE:                          10 (unmanaged)
    GENERAL.CONNECTION:                     --
    GENERAL.CON-PATH:                       --
    IP4.ADDRESS[1]:                         127.0.0.1/8
    IP4.GATEWAY:                            --
    IP6.ADDRESS[1]:                         ::1/128
    IP6.GATEWAY:                            --
    IP6.ROUTE[1]:                           dst = ::1/128, nh = ::, mt = 256

You may then use ``ping`` or other network utilities to check your connectivity.
