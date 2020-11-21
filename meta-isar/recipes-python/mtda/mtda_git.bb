# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "4e70dc9fe245c046a2608f217b5577b8631f45f5"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
