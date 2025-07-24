# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2025 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg-raw

PR = "1"
CHANGELOG_V = "${PV}-${PR}"

do_install[network] = "${TASK_USE_NETWORK}"
do_install() {
    mkdir -p ${D}/opt/whl
    python3 -m pip download pytest==${PV} -d ${D}/opt/whl
}
