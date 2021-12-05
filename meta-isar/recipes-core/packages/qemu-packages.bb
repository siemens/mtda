# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# Here's our list of custom packages for qemu
DEPENDS = "  \
    gnutls28 \
"

# Make sure packages we built were added to the isar-apt repository
do_build[deptask] += "do_deploy_deb"

# This is a meta-package, nothing to build per se
do_build() {
    true
}

do_deploy_deb() {
    true
}
addtask deploy_deb after do_build
