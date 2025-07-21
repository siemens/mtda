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
    mtda-cli \
    mtda-service \
    mtda-systemd-helper \
    mtda-www \
    mtda.ini \
    mtda/ \
    scripts/ \
    setup.py \
    tests/ \
    tox.ini \
    "

# Here's our list of custom packages
RDEPENDS:${PN} = "                       \
    python3-hap-python                   \
    mjpg-streamer                        \
    mtda                                 \
    pyodide                              \
    sd-mux-ctrl                          \
"
# Ubuntu noble ships sd-mux-ctrl package
RDEPENDS:${PN}:remove:noble = "sd-mux-ctrl"

PROVIDES += "                            \
    mtda-service                         \
    mtda-client                          \
    mtda-common                          \
    mtda-docker                          \
    mtda-kvm                             \
    mtda-pytest                          \
    mtda-www                             \
"

SRC_URI += "${@' '.join(['file://' + d.getVar('LAYERDIR_mtda') + '/../' + file for file in d.getVar('MTDA_FILES').split()])}"

S = "${WORKDIR}/working-repo"

do_gen_working_repo() {
	for file in ${MTDA_FILES}; do
		cp -a ${LAYERDIR_mtda}/../$file ${S}/
	done
	rm -f ${S}/debian/source/format
}
do_gen_working_repo[cleandirs] += "${S}"

addtask gen_working_repo after do_fetch before do_unpack
