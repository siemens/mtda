# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "863c417746a7edd2bc00be1a14a17f97160bb2ec"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
