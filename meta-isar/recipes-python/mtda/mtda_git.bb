# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "2b1260c575490bf79cb394b8e5f3d2d1573d91b3"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
