# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2025 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

require recipes-bsp/u-boot/u-boot-custom.inc

# u-boot tools need OpenSSL headers/libraries
DEBIAN_BUILD_DEPENDS:append = ",libssl-dev:native,libssl-dev"

# Python packages needed during the build
DEBIAN_BUILD_DEPENDS:append = ",python3-distutils,python3-pkg-resources,python3-all-dev:native,swig"
