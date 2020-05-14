# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "f2af34b35b931b83e5bd018f946d4a0af9af21f3"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
