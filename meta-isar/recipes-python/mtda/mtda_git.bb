# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "e22a9f8c71fd2285a3ecc08f2cc064fe7a76f983"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
