# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "b89aed0c09ff963dd9a4bb613869ba4e7259c41b"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
