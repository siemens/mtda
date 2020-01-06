# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "fb4575e30d77938a539975b1f2759c61ca7f21b7"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
