# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "d5347de23ea950f94e48569894ca0f99400c7b9f"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
