# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/zerorpc-python.git;protocol=https;branch=debian/0.6.3"
SRCREV   = "145d70032e9cc9c78ad3b1c545204333a65d578b"
S        = "${WORKDIR}/git"

do_prepare_build_append() {
    echo "DEB_BUILD_OPTIONS += nocheck" >>${S}/debian/rules
}
