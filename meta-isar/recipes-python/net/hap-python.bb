# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

PV = "3.0"

SRC_URI = " \
    git://github.com/ikalchev/HAP-python.git;protocol=https;branch=master;destsuffix=${PN}-${PV}/ \
    file://${PN}-${PV} \
"

SRCREV = "d3c576c4d6cc8af4516a99c30042bb01dbd0a100"

DEPENDS = "curve25519-donna ed25519 zeroconf"
do_build[deptask] += "do_deploy_deb"
