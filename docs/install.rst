Installation
============

Using apt
---------

Packages for Debian 11 (bullseye) may be installed as follows::

   $ echo 'deb [trusted=yes] https://apt.fury.io/mtda/ /' | \
     sudo tee /etc/apt/sources.list.d/mtda.list
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
