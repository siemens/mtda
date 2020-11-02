Use with LAVA
=============

Installing LAVA on Debian
-------------------------

A LAVA instance may be installed on Debian with ``apt``::

    $ sudo apt install -y lava

Create ``/etc/lava-server/settings.conf`` with the following settings for a
simple installation::

    "ALLOWED_HOSTS": ["infra-lava.lan"]
    "CSRF_COOKIE_SECURE": false
    "SESSION_COOKIE_SECURE": false

Replace ``infra-lava.lan`` with the network name of your Debian server. A super
user should be created::

    $ sudo lava-server manage createsuperuser --username john --email=john@foo.com

The web interface should be enabled with::

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
``ssh`` (default credentials are ``mdta``/``mtda``)::

    $ ssh mtda@mtda-for-de0-nano-soc.lan

Use ``vi`` to edit ``/etc/lava-dispatcher/lava-slave``::

    $ sudo vi /etc/lava-dispatcher/lava-slave

and set the following variables to match your network::

    MASTER_URL="tcp://infra-lava.lan:5556"
    LOGGER_URL="tcp://infra-lava.lan:5555"
    HOSTNAME="--hostname mtda-for-de0-nano-soc.lan"

The service should be restarted::

    $ sudo systemctl restart lava-slave

Adding support for devices attached to MTDA
-------------------------------------------

A ``mtda`` device type may be added to your LAVA installation and used as a
base for devices added to your LAVA instance. Create
``/etc/lava-server/dispatcher-config/device-types/mtda.jinja2`` as follows::

    {# device_type: mtda #}
    {% extends 'base.jinja2' %}

    {% set connection_command = 'mtda-cli -r localhost console raw' %}
    {% set power_off_command = 'mtda-cli -r localhost target off' %}
    {% set power_on_command = 'mtda-cli -r localhost target on' %}
    {% set hard_reset_command = 'mtda-cli -r localhost target reset' %}
    {% set flasher_deploy_commands = ['mtda-cli -r localhost target off',
                                      'mtda-cli -r localhost storage host',
                                      'mtda-cli -r localhost storage write "{IMAGE}"',
                                      'mtda-cli -r localhost storage target'] %}

    {% block body %}

    actions:
      deploy:
        methods:
    {% if flasher_deploy_commands %}
          flasher:
            commands: {{ flasher_deploy_commands }}
    {% endif %}
      boot:
        connections:
          serial:
        methods:
          minimal:
    {% endblock body %}

    {% block timeouts %}
    timeouts:
      actions:
        bootloader-retry:
          minutes: 2
        bootloader-interrupt:
          minutes: 5
        bootloader-commands:
          minutes: 5
      connections:
        bootloader-retry:
          minutes: 2
        bootloader-interrupt:
          minutes: 5
        bootloader-commands:
          minutes: 5
    {% endblock timeouts %}
