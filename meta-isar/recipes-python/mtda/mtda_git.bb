# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "dc5c6c20aa9233f55c0538cd22c98ac65d189dfd"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
