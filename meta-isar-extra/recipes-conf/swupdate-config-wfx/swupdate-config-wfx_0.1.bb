# This Isar layer is part of MTDA
# Copyright (C) 2025 Siemens AG
# SPDX-License-Identifier: MIT

DESCRIPTION = "WFX backend configuration for swupdate"
MAINTAINER = "mtda-users <mtda-users@googlegroups.com>"

WFX_TENANT ??= "default"
WFX_SERVER ??= "http://localhost:8080"

SRC_URI = "file://wfx.conf.tmpl"

TEMPLATE_FILES += "wfx.conf.tmpl"
TEMPLATE_VARS += " \
    WFX_SERVER \
    WFX_TENANT \
"

inherit dpkg-raw

do_install() {
    install -d ${D}/etc/swupdate/conf.d
    install -m 0644 ${WORKDIR}/wfx.conf ${D}/etc/swupdate/conf.d/wfx.conf
}
