# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "13f7b0ce98deab933a31505508f5591aa2ede85a"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
