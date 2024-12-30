# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2025 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

SRC_URI = " \
    https://files.pythonhosted.org/packages/59/29/d557718c84ef1a8f275faa4caf8e353778121beefbe9fadfa0055ca99aae/${PN}-${PV}.tar.gz \
    file://${PN}-${PV}/debian \
"

SRC_URI[sha256sum] = "bed2cc2216f538eca4255a83a4588d8823563cdd50114f86cf1a2674e602c93c"
