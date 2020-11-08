# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "7ae8f6cf69ce6028b4da7fb8994d57e320067ee8"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
