# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "0527668b518141f0cd0bd5814b5d0df739f6a829"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
