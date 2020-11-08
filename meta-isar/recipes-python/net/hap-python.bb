# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

PV = "3.0"

SRC_URI = " \
    git://github.com/ikalchev/HAP-python.git;protocol=https;destsuffix=${PN}-${PV}/ \
    file://${PN}-${PV} \
"

SRCREV = "d3c576c4d6cc8af4516a99c30042bb01dbd0a100"

DEPENDS = "curve25519-donna ed25519 zeroconf"
do_build[deptask] += "do_deploy_deb"
