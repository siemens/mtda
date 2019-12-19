# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "37b8e38dc1437058ca634bc96f17451d61a9f161"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
