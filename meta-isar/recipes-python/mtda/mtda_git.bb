# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "99946705d5f896473027afe08b31d1f75977870e"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
