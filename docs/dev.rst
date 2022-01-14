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
drivers we provide::

    $ cp configs/docker.ini mtda.ini

The agent may then be started with::

    $ export PYTHONPATH=$PWD
    $ ./mtda-cli -d -n

Use a different shell to start a client session::

    $ cd mtda
    $ export PYTHONPATH=$PWD
    $ ./mtda-cli target on
    $ ./mtda-cli

The container should be running. Hit return to get a shell prompt and run any
shell commands available in the container selected in your ``mtda.ini`` file.
