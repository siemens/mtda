# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "be728a6f4f4cc2294c2e80b6024bf807f7bd05cf"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
