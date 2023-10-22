Installation
============

Using apt on Debian 12
----------------------

Set up MTDA apt repository::

   # Add MTDA's GPG key:
   $ sudo install -m 0755 -d /etc/apt/keyrings
   $ curl -fsSL https://apt.fury.io/mtda/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/mtda.gpg
   $ sudo chmod a+r /etc/apt/keyrings/mtda.gpg

   # Add repository to Apt sources
   $ echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/mtda.gpg] https://apt.fury.io/mtda/ /" | sudo tee /etc/apt/sources.list.d/mtda.list
     deb [arch=amd64 signed-by=/etc/apt/keyrings/mtda.gpg] https://apt.fury.io/mtda/ /

Packages for Debian 12 (bookworm) may be installed as follows::

   $ sudo apt-get update
   $ sudo apt-get install -y mtda

Using apt on Ubuntu 22.04
-------------------------

Packages for Ubuntu 22.04 (Jammy Jellyfish) may be installed as follows::

   $ sudo add-apt-repository ppa:chombourger/mtda-jammy
   $ sudo apt-get update
   $ sudo apt-get install -y mtda

Using pip
---------

The latest released version may be installed using pip::

    $ pip3 install --user mtda

You may alternatively fetch the latest version from GitHub and install it as
follows::

    $ git clone https://github.com/siemens/mtda
    $ cd mtda
    $ pip3 install --user .

You may check your installation with the ``help`` command::

    $ export PATH=$HOME/.local/bin:$PATH
    $ mtda-cli help

Using apt for installing mtda-docker and mtda-kvm
-------------------------------------------------

Docker and KVM may be used as virtual platforms by respectively installing the mtda-docker and mtda-kvm packages from the Apt package feeds described above.

`mtda-docker` may be installed as follows::

    $ sudo apt-get install mtda-docker
    $ sudo mkdir -p /etc/mtda/
    $ sudo cp /usr/share/doc/mtda-docker/examples/docker.ini /etc/mtda/config

`mtda-kvm` may be installed as follows::

    $ sudo apt-get install mtda-kvm
    $ sudo mkdir -p /etc/mtda/
    $ sudo cp /usr/share/doc/mtda-kvm/examples/qemu.ini /etc/mtda/config
