Development
===========

Contributions are welcome from anyone. This section provides guidelines for
setting up your environment to run a development copy of MTDA on your system
without requiring special hardware either using Docker or KVM.

Docker
~~~~~~

Docker is a popular container technology and it may be used as a virtual test
platform to develop general purpose tests or APIs for MTDA.

MTDA requires several Python packages, it is recommended to install them using
``pip`` and under your user to leave your system intact. Use ``apt`` to install
``pip``::

    $ sudo apt-get install -y python3-pip

and modify your environment to have the shell look for programs in
``$HOME/.local/bin``::

    $ echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc

The docker engine may be installed as follows on Debian::

    $ sudo apt-get install -y docker.io
    $ sudo /sbin/adduser $USER docker
    $ sudo systemctl enable docker
    $ sudo systemctl start docker

It is recommended to leave your session and start a new one if your user account
did not belong to the ``docker`` group before. You may then check if docker is
up and running::

    $ docker images

You may then get a copy of the MTDA code with::

    $ git clone https://github.com/siemens/mtda

and required Python packages and MTDA may be installed with::

    $ cd mtda
    $ pip3 install --user .

A configuration file is then needed for MTDA to use the various ``docker``
drivers using the ``MTDA_CONFIG`` environment variable.

The agent may then be started with::

    $ export MTDA_CONFIG=$PWD/configs/docker.ini
    $ export PYTHONPATH=$PWD
    $ ./mtda-service -n

Use a different shell to start a client session::

    $ cd mtda
    $ export MTDA_CONFIG=$PWD/configs/docker.ini
    $ export PYTHONPATH=$PWD
    $ ./mtda-cli target on
    $ ./mtda-cli

The container should be running. Hit return to get a shell prompt and run any
shell commands available in the container selected in your ``MTDA_CONFIG``
file.

Release Process
---------------

There are certain steps that needs to be done when making a release. This
checklist here serves as guidance to the one in charge of making a new release.
Roughly start with this 2-3 weeks before the targeted release date.

+------+---------------------------------------------------+------------+
| When | Action                                            | Example    |
+======+===================================================+============+
| -3w  | Create -tc1 tag                                   | v0.16-tc1  |
+------+---------------------------------------------------+------------+
| -3w  | Inform maintainers about upcoming release         |            |
+------+---------------------------------------------------+------------+
| -1w  | Collect ``Tested-by:`` tags                       |            | 
+------+---------------------------------------------------+------------+
| -1w  | Draft ``debian/changelog``                        |            |
+------+---------------------------------------------------+------------+
| -1w  | Create -rc1 tag                                   | v0.16-rc1  |
+------+---------------------------------------------------+------------+
|  0d  | Create release tag                                | v0.16      |
+------+---------------------------------------------------+------------+
|  0d  | Move open issues to next milestone                |            |
+------+---------------------------------------------------+------------+
|  0d  | Send release announcement                         |            |
+------+---------------------------------------------------+------------+
|  0d  | Create new version in ``debian/changelog``        |            |
|      | suffixed with "-0" (e.g. 0.18-0)                  |            |
+------+---------------------------------------------------+------------+

GitHub actions will build the final release tag and upload artifacts such as
Debian packages to fury.io and Ubuntu packages to our PPA.
