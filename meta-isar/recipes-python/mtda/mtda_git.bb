# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "438aa9141bc0e7e377f2fdae16249aab55483b9c"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
