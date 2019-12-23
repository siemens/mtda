# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

DESCRIPTION = "set system hostname to mtda"
MAINTAINER = "Cedric Hombourger <chombourger@gmail.com>"
DEBIAN_DEPENDS = "base-files"

SRC_URI = "file://postinst"

inherit dpkg-raw

do_install() {
    true
}
