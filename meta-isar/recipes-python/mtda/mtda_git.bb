# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "4adf65c62dcb4523b9d2e82a9e7e0139f726f6d8"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
