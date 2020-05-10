# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "e31d60a322bd624f3be1737ac8a8894062b09b6a"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
