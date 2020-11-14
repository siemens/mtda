# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "c7ce9c6584316e0f3a3056f753353e184bfc7b0b"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
