# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2025 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

PV = "4.9.2"

SRC_URI = " \
    git://github.com/ikalchev/HAP-python.git;protocol=https;branch=dev;destsuffix=${PN}-${PV}/ \
    file://${PN}-${PV} \
"

SRCREV = "86ed133f258c770fb348232b1cab4b781139fd95"

PROVIDES += "python3-hap-python"
do_build[deptask] += "do_deploy_deb"
