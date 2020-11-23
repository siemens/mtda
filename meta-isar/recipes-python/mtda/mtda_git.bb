# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "3bc5ef35b2636d6c3ef95cc1a14f18ad80bf1df3"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
