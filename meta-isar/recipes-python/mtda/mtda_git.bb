# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "b55fc03941c3b3d12d758daa62ad747f99450eb3"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
