# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "3644998b6a6fe20787d5a081eac2302009a35681"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
