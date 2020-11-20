# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "4071a9201b0f91f678c9d598100c8eca9054c93b"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
