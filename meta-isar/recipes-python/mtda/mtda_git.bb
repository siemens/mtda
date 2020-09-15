# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "4e313636d57a38015dfd4772f6de44d7cd691a26@
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
