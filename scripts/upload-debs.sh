#!/bin/bash
# ---------------------------------------------------------------------------
# Upload MTDA packages to bintray
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (c) Mentor, a Siemens business, 2017-2020
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# Our bintray API key is required, abort if missing
if [ -z "${BINTRAYAPIKEY}" ]; then
    echo "Missing API key!" >&2
    exit 1
fi

# Our GPG passphrase is also required, also abort if missing
if [ -z "${BINTRAYPASS}" ]; then
    echo "Missing passphrase!" >&2
    exit 1
fi

# MTDA release date and version
MTDA_DATE=$(date +%Y-%m-%d)
MTDA_VERSION=$(python3 -c 'import mtda; print(mtda.__version__)')

# Abort if a command fails
set -e

# Replace MTDA variables in config file
config_json=$(mktemp)
sed -e "s,@MTDA_DATE@,${MTDA_DATE},g" \
    -e "s,@MTDA_VERSION@,${MTDA_VERSION},g" \
    configs/bintray.json >${config_json}

# Copy Debian packages from the Isar build
mkdir -p deploy-armhf
find build-armhf/build/tmp/deploy/isar-apt/apt -name *.deb -exec cp {} deploy-armhf/ \;

# Upload them to bintray
dpl --provider=bintray            \
    --file="${config_json}"       \
    --skip_cleanup                \
    --user="chombourger"          \
    --key="${BINTRAYAPIKEY}"      \
    --passphrase="${BINTRAYPASS}"
