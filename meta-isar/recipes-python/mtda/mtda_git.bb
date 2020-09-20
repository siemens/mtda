# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "f2fe626554511460fbcacc2fc033b66655946121"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
