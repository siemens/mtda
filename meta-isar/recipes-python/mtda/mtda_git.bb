# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "dac17ebfd77a170a131be58404484192ea838960"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
