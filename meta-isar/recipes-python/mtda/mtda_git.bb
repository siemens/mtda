# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "bba4234f66542b4d6ee7c0d0d0b04bc839e7eea9"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
