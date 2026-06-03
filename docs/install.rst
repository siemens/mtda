Installation
============

Using apt on Debian 13
----------------------

Set up MTDA apt repository::

   # Add MTDA's GPG key:
   $ sudo install -m 0755 -d /etc/apt/keyrings
   $ curl -fsSL https://apt.fury.io/mtda-trixie/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/mtda.gpg
   $ sudo chmod a+r /etc/apt/keyrings/mtda.gpg

   # Add repository to Apt sources
   $ echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/mtda.gpg] https://apt.fury.io/mtda-trixie/ /" | sudo tee /etc/apt/sources.list.d/mtda.list

Packages for Debian 13 (trixie) may be installed as follows::

   $ sudo apt-get update
   $ sudo apt-get install -y mtda

Using apt on Debian 12
----------------------

Set up MTDA apt repository::

   # Add MTDA's GPG key:
   $ sudo install -m 0755 -d /etc/apt/keyrings
   $ curl -fsSL https://apt.fury.io/mtda/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/mtda.gpg
   $ sudo chmod a+r /etc/apt/keyrings/mtda.gpg

   # Add repository to Apt sources
   $ echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/mtda.gpg] https://apt.fury.io/mtda/ /" | sudo tee /etc/apt/sources.list.d/mtda.list

Packages for Debian 12 (bookworm) may be installed as follows::

   $ sudo apt-get update
   $ sudo apt-get install -y mtda

Using apt on Ubuntu 24.04
-------------------------

Packages for Ubuntu 24.04 (Noble Numbat) may be installed as follows::

   $ sudo add-apt-repository ppa:chombourger/mtda-noble
   $ sudo apt-get update
   $ sudo apt-get install -y mtda

Using uv (Recommended for Development)
--------------------------------------

`uv <https://github.com/astral-sh/uv>`_ is a fast, modern Python package manager. It's recommended for development and local installations.

Install uv::

    $ curl -LsSf https://astral.sh/uv/install.sh | sh

Install MTDA from PyPI::

    $ uv tool install mtda

Or install from source for development::

    $ git clone https://github.com/siemens/mtda
    $ cd mtda
    $ uv sync --all-extras

This creates a virtual environment in ``.venv/`` and installs MTDA with all optional dependencies.

Activate the environment and verify installation::

    $ source .venv/bin/activate
    $ mtda-cli --version

**Platform-specific installation:**

On Linux (with systemd support)::

    $ uv tool install "mtda[linux]"

On macOS (client only, no systemd)::

    $ uv tool install mtda

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
    $ sudo cp /usr/share/doc/mtda-docker/examples/mtda.ini /etc/mtda/config

`mtda-kvm` may be installed as follows::

    $ sudo apt-get install mtda-kvm
    $ sudo mkdir -p /etc/mtda/
    $ sudo cp /usr/share/doc/mtda-kvm/examples/mtda.ini /etc/mtda/config
