# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "d970c4a576994088cf0a648a188f94695969619f"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
