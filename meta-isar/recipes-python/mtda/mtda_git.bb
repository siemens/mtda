# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "be4d9f3ac6955de4465310ab44bcbc4b9b085787"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
