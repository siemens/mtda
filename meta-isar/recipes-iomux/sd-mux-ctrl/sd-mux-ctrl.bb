# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

PV = "0.0.3"
PR = "3"

SRC_URI = "http://deb.debian.org/debian/pool/main/s/${PN}/${PN}_${PV}-${PR}.dsc;name=dsc  \
           http://deb.debian.org/debian/pool/main/s/${PN}/${PN}_${PV}.orig.tar.bz2;name=orig;unpack=false  \
           http://deb.debian.org/debian/pool/main/s/${PN}/${PN}_${PV}-${PR}.debian.tar.xz;name=debian;unpack=false"

SRC_URI[dsc.sha256sum] = "94a44dc24ace30e336f6ac2d920bfea55909d30cfdbeb0333c04b017c74ee4e9"
SRC_URI[orig.sha256sum] = "180db298620147362f30681854370a9c38793ca295ac3b016e4dc518352e44a7"
SRC_URI[debian.sha256sum] = "4fb4b223ce973f8317910b36de3cb19c20cdfcf778dcee554ae14ff77839f7dd"

do_prepare_build(){
    dpkg-source -x ${WORKDIR}/${PN}_${PV}-${PR}.dsc ${S}
}
