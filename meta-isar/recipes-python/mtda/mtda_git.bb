# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "eb95d0db07d28b2baedf111c17ab931e9ffa3e0f"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
