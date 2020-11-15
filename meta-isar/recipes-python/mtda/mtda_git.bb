# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "accf82c99aa3bc208e59bd0a14097f0d0ee1fd5f"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
