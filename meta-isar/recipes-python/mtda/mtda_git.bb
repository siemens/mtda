# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "0dd669e562e1d0bec9daa02dcf40ff2aabc24913"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
