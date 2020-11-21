# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "82c28ca4652becdfbdede7b0b4d2120d5c8f5eaa"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
