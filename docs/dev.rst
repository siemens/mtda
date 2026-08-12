Development
===========

Contributions are welcome from anyone. This section provides guidelines for
setting up your environment to run a development copy of MTDA on your system
without requiring special hardware either using Docker or KVM.

Development Setup
~~~~~~~~~~~~~~~~~

Setting up a development environment for MTDA is straightforward using modern
Python tooling. We recommend using ``uv`` for fast, reliable dependency
management.

Install uv
^^^^^^^^^^

Install ``uv`` (a fast Python package manager)::

    $ curl -LsSf https://astral.sh/uv/install.sh | sh

Clone the repository
^^^^^^^^^^^^^^^^^^^^

Get a copy of the MTDA code::

    $ git clone https://github.com/siemens/mtda
    $ cd mtda

Install dependencies
^^^^^^^^^^^^^^^^^^^^

Use ``uv sync`` to create a virtual environment and install all dependencies::

    $ uv sync --all-extras

This command will:

- Create a ``.venv/`` directory with a virtual environment
- Install MTDA in editable mode
- Install all optional dependencies (dev, docs, linux on Linux systems)
- Generate/verify gRPC stubs automatically

On macOS (client-only development)::

    $ uv sync --extra dev --extra docs

Activate the environment
^^^^^^^^^^^^^^^^^^^^^^^^^

Activate the virtual environment::

    $ source .venv/bin/activate

Verify the installation::

    $ mtda-cli --version

Running commands
^^^^^^^^^^^^^^^^

With the virtual environment activated, you can run MTDA commands directly::

    $ mtda-cli --help
    $ mtda-service --help

Or use ``uv run`` without activating::

    $ uv run mtda-cli --help
    $ uv run pytest
    $ uv run flake8

Docker Development Platform
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Docker is a popular container technology and it may be used as a virtual test
platform to develop general purpose tests or APIs for MTDA.

Install Docker
^^^^^^^^^^^^^^

The docker engine may be installed as follows on Debian::

    $ sudo apt-get install -y docker.io
    $ sudo /sbin/adduser $USER docker
    $ sudo systemctl enable docker
    $ sudo systemctl start docker

It is recommended to leave your session and start a new one if your user account
did not belong to the ``docker`` group before. You may then check if docker is
up and running::

    $ docker images

Running with Docker
^^^^^^^^^^^^^^^^^^^

After setting up your development environment (see above), start the MTDA
service with a Docker configuration::

    $ export MTDA_CONFIG=$PWD/configs/docker.ini
    $ uv run mtda-service -n

Use a different shell to start a client session::

    $ cd mtda
    $ export MTDA_CONFIG=$PWD/configs/docker.ini
    $ uv run mtda-cli target on
    $ uv run mtda-cli

The container should be running. Hit return to get a shell prompt and run any
shell commands available in the container selected in your ``MTDA_CONFIG``
file.

Regenerating gRPC Stubs
~~~~~~~~~~~~~~~~~~~~~~~

gRPC stubs are auto-generated at build time and are NOT committed to git.
If you modify ``mtda/grpc/mtda.proto``, regenerate stubs locally for testing::

    $ python scripts/generate-grpc-stubs.py --force

This will:

- Run ``protoc`` to generate Python stubs from the .proto file
- Fix imports for proper package usage
- Create ``mtda/grpc/mtda_pb2.py`` and ``mtda/grpc/mtda_pb2_grpc.py``

These generated files should not be committed to version control.

Running Tests
~~~~~~~~~~~~~

Run the test suite::

    $ uv run pytest

Run code linters::

    $ uv run flake8
    $ uv run reuse lint

Run tests in Docker containers (as done in CI)::

    $ uv run bash ./scripts/test-using-docker

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
