# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "c966f0b2daf1cd7f427eebf0bd37a7a3b73a5dae"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
