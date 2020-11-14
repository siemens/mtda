# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "758e5cebc1a3074a2dce3a7d8a43bf464fa86b34"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
