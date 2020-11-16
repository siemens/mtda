# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "101bbd3851d1519d923a4f8f7088751beec76ee9"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
