# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "b71c8fbb5981f54612ccbf802cc11c55289a76e0"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
