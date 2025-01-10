
# Overview

Multi-Tenant Device Access (or MTDA for short) is a relatively small Python application
acting as an interface to a test device. It provides mechanisms to remotely turn the
device on or off (assuming an IP/USB power switch is available), plug USB devices in
or out (also requiring special hardware) or simply access its console (in most cases
serial).

A sample setup is depicted below:

![NanoPI setup](docs/neo_block_diagram.png)

# Badges

[![CI](https://github.com/siemens/mtda/actions/workflows/main.yml/badge.svg)](https://github.com/siemens/mtda/actions/workflows/main.yml)
[![DOCS](https://readthedocs.org/projects/mtda/badge/?version=latest)](https://mtda.readthedocs.io/en/latest/?badge=latest)
[![REUSE](https://api.reuse.software/badge/github.com/siemens/mtda)](https://api.reuse.software/info/github.com/siemens/mtda)

# Getting Started

 * [Installation](https://mtda.readthedocs.io/en/latest/install.html)
 * [Usage](https://mtda.readthedocs.io/en/latest/usage.html)
 * [Configuration](https://mtda.readthedocs.io/en/latest/config.html)
 * [Build Your Own](https://mtda.readthedocs.io/en/latest/build.html)

# Development

Mailing list:
* `mtda-users@googlegroups.com`

Archive:
[https://www.mail-archive.com/mtda-users@googlegroups.com/](https://www.mail-archive.com/mtda-users@googlegroups.com)

For sending patches, please refer to the mailing list and `CONTRIBUTING.md` in
the source tree.

# License

MTDA is licensed under the [MIT](https://opensource.org/licenses/MIT) license.
