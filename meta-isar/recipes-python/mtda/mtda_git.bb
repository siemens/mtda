# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2025 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

MTDA_FILES = " \
    CONTRIBUTING.md \
    COPYING \
    LICENSES/ \
    MAINTAINERS.md \
    MANIFEST.in \
    README.md \
    configs/ \
    debian/ \
    docs/ \
    Kconfig \
    mtda-cli \
    mtda-config \
    mtda-service \
    mtda-systemd-helper \
    mtda-ui \
    mtda-www \
    mtda.ini \
    mtda/ \
    scripts/ \
    setup.py \
    tests/ \
    tox.ini \
    "

SRC_URI += "${@' '.join(['file://' + d.getVar('LAYERDIR_mtda') + '/../' + file for file in d.getVar('MTDA_FILES').split()])}"

S = "${WORKDIR}/working-repo"

DEPENDS += "py3qterm"

do_gen_working_repo() {
	for file in ${MTDA_FILES}; do
		cp -a ${LAYERDIR_mtda}/../$file ${S}/
	done
	rm -f ${S}/debian/source/format
}
do_gen_working_repo[cleandirs] += "${S}"

addtask gen_working_repo after do_fetch before do_unpack
