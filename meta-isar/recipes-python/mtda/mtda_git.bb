# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "6b050cc8ec25a550cb6374fe10db975429a720ae"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
