# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

require u-boot-${PV}.inc

# u-boot tools need OpenSSL headers/libraries
DEBIAN_BUILD_DEPENDS_append = ",libssl-dev:native,libssl-dev"

# Python packages needed during the build
DEBIAN_BUILD_DEPENDS_append = ",python3-distutils,python3-pkg-resources,python3-all-dev:native,swig"

U_BOOT_BIN = "u-boot-sunxi-with-spl.bin"
U_BOOT_CONFIG = "nanopi_r1_defconfig"

SRC_URI += "file://add-nanopi-r1.patch"

dpkg_runbuild_prepend() {
    sed -i -e 's,U_BOOT_BIN,U_BOOT_TARGET,g' ${S}/debian/rules
}
