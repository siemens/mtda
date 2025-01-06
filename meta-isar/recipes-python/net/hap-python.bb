# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2025 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

PV = "4.9.1"

SRC_URI = " \
    git://github.com/ikalchev/HAP-python.git;protocol=https;branch=master;destsuffix=${PN}-${PV}/ \
    file://${PN}-${PV} \
"

SRCREV = "5265b54f707a50df72d25de5c24529b74eac4c63"

PROVIDES += "python3-hap-python"
do_build[deptask] += "do_deploy_deb"
