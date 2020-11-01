Use with LAVA
=============

Installing LAVA on Debian
-------------------------

A LAVA instance may be installed on Debian with ``apt``:

    $ sudo apt install -y lava

Create ``/etc/lava-server/settings.conf`` with the following settings for a
simple installation:

    "ALLOWED_HOSTS": ["infra-lava.lan"]
    "CSRF_COOKIE_SECURE": false
    "SESSION_COOKIE_SECURE": false

Replace ``infra-lava.lan`` with the network name of your Debian server. A super
user should be created:

    $ sudo lava-server manage createsuperuser --username john --email=john@foo.com

The web interface should be enabled with:

    $ sudo a2dissite 000-default
    $ sudo a2enmod proxy
    $ sudo a2enmod proxy_http
    $ sudo a2ensite lava-server.conf
    $ sudo service apache2 restart
    $ sudo service lava-server-gunicorn restart

Attaching your MTDA device to LAVA
----------------------------------

The sample NanoPI NEO image comes with the ``lava-dispatcher`` package
pre-installed. It however needs to be configured to connect to the LAVA master
and logger installed as noted above. You may connect to the MTDA agent using
``ssh`` (default credentials are ``mdta``/``mtda``):

    $ ssh mtda@mtda-for-de0-nano-soc.lan

Use ``vi`` to edit ``/etc/lava-dispatcher/lava-slave``:

    $ sudo vi /etc/lava-dispatcher/lava-slave

and set the following variables to match your network:

    MASTER_URL="tcp://infra-lava.lan:5556"
    LOGGER_URL="tcp://infra-lava.lan:5555"
    HOSTNAME="--hostname mtda-for-de0-nano-soc.lan"

The service should be restarted:

    $ sudo systemctl restart lava-slave
