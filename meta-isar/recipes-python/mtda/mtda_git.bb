# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "fd183727fa7f288d25cc90608698f4e152faf177"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
