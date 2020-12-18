# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "f0b815b2967bf3569597cacb0966cfe5c34fe031"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
