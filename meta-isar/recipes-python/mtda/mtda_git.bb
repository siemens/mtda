# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "d32a063b4aa8a4b5cccb63069a114a87937f42a2"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
