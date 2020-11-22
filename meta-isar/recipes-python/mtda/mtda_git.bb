# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "f1186e67c41e7cf5673ca032008f24c02412b18a"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
