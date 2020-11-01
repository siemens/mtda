# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "cef8b68f16780765881fb0d3cc5e81d29a75b7d6"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
