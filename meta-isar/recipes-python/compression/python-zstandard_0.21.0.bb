# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2023 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

GH_URI  = "https://github.com/indygreg/${PN}/archive/refs/tags/${PV}.tar.gz"
SRC_URI = "${GH_URI} file://debian-compat.patch"
SRC_URI[sha256sum] = "15adc6bfa629d48b0bb658e9eae94c484adb66a28738fa780478eebeb41599a5"

DEB_BUILD_OPTIONS  = "nocheck"
ISAR_CROSS_COMPILE = "0"
