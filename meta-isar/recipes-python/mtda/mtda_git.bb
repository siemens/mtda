# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "b4a21c28c6376559007c3ac0505d7648c4f9707e"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
