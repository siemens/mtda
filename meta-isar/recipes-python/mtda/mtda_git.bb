# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "584487e69450d31949dc57e5f0eb91a09f861547"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
