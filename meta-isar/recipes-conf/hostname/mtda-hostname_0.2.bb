# This Isar layer is part of MTDA
# Copyright (C) 2017-2021 Mentor Graphics, a Siemens business
# SPDX-License-Identifier: MIT

DESCRIPTION = "set system hostname to mtda"
MAINTAINER = "Cedric Hombourger <chombourger@gmail.com>"
DEBIAN_DEPENDS = "base-files"
DPKG_ARCH = "all"

SRC_URI = "file://postinst"

inherit dpkg-raw

do_install() {
    true
}
