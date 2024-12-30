# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2025 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

GH_URI  = "https://github.com/indygreg/${PN}/archive/refs/tags/${PV}.tar.gz"
SRC_URI = "${GH_URI} file://debian-compat.patch"
SRC_URI[sha256sum] = "34ce7ef020afca1344c538a778e2a2e30dc43b11509aa4cb5cf076228d959ca7"

DEB_BUILD_OPTIONS  = "nocheck"
ISAR_CROSS_COMPILE = "0"
