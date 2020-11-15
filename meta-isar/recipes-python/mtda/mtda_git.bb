# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "ac3dc77951f26cbd2c13edfa3e1a95b6e7ee5004"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
