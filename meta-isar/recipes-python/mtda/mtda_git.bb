# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "0f28125512c455f27f399c723252bfafdeab9da7"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
