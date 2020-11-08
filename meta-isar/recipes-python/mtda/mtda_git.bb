# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "48e1d34f1fcd619dc88dfb2722d1d3b7847a0ee6"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
