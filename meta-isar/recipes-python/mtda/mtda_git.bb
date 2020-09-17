# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "50f57a4bf10bb0bf2e011c240b0e31b0014571c8"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
