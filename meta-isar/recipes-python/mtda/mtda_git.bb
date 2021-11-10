# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://git@github.com/MentorEmbedded/mtda.git;protocol=ssh;branch=master"
SRCREV   = "63a982597916e53ac8dec4342390e62a59891f48"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
