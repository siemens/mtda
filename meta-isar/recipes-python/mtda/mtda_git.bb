# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "7fea128c2a6ed8d1a44da8c5b6311be97fd6415a"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
