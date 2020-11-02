# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "48487ea36a96c2e8da78e062d631fa6b7d0eea5f"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
