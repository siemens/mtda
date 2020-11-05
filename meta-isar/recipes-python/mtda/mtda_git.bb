# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "4ceca7b2df06f2ae701379c5b1a599a01e5176c5"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
