# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

SRC_URI = "apt://${PN} \
           file://changelog.tmpl "

DEB_BUILD_OPTIONS += "nocheck"

do_prepare_build() {
    cd ${S}
    grep -q libtspi-dev debian/control || \
    sed -i '/libtasn1-6-dev/a \ libtspi-dev,' debian/control
    grep -q with-tpm debian/rules || \
    sed -i -e 's/without-tpm/with-tpm/g' debian/rules
    version=$(dpkg-parsechangelog -S Version)
    version="${version}+mtda"
    cd ${WORKDIR}
    cat changelog.tmpl | CHANGELOG_V=${version} envsubst '$CHANGELOG_V' > changelog
    grep -q ${version} ${S}/debian/changelog || \
    sed -i -e '1rchangelog' -e '1{h;d}' -e '2{x;G}' ${S}/debian/changelog
    touch --reference changelog.tmpl \
        ${S}/debian/changelog \
        ${S}/debian/control \
        ${S}/debian/rules
}
