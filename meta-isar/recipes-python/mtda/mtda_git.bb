# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "f3ae7867722278e3c81b051c9d9f7bc3f02a1de6"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
