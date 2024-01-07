# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2024 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

ORIG_URI = "https://files.pythonhosted.org/packages/fa/7f/a2d1aace16ef44ffa51d51e4cf6e5e50c1bfaf9f61d5d596318d410d7e85/${PN}-${PV}.tar.gz"

SRC_URI = " \
    ${ORIG_URI} \
    ${ORIG_URI};unpack=no;downloadfilename=${PN}_${PV}.orig.tar.gz \
    file://${PN}-${PV}/debian \
"

S = "${WORKDIR}/${PN}-${PV}"
SRC_URI[sha256sum] = "88379580d5d155361e072520bae62e047ab3741eaeb8b07867ab4588ea7a5031"
