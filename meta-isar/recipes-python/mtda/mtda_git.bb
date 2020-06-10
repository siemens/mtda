# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "12ef6750800d22d708447902ba5d350dd1e408db"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
