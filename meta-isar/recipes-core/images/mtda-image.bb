# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2025 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit image

DESCRIPTION = "Debian image for MTDA assist boards"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${LAYERDIR_core}/licenses/COPYING.MIT;md5=838c366f69b72c5df05c96dff79b35f2"

PV = "1.0"

ISAR_RELEASE_CMD = "git -C ${LAYERDIR_mtda} describe --tags --dirty --match 'v[0-9].[0-9]*'"

# We suffix u-boot-script with DISTRO and MACHINE, remove the non-suffixed
# version of the package
IMAGE_INSTALL:remove = "u-boot-script"

# Custom u-boot script for the beaglebone-black
IMAGE_INSTALL:append:beaglebone-black = " u-boot-script-${DISTRO}-${MACHINE}"

# Custom u-boot script for the nanopi-neo
IMAGE_INSTALL:append:nanopi-neo = " u-boot-script-${DISTRO}-${MACHINE}"

# Custom u-boot and script for the nanopi-r1
DEPENDS:append:nanopi-r1 = " u-boot-nanopi-r1"
IMAGE_INSTALL:append:nanopi-r1 = " u-boot-script-${DISTRO}-${MACHINE}"

IMAGE_INSTALL += "                       \
    mtda                                 \
    mtda-www                             \
    mtda-hostname                        \
    mtda-network                         \
    mtda-repo                            \
    local-settings                       \
    sshd-regen-keys                      \
"

IMAGE_PREINSTALL += "                    \
    iproute2                             \
    isc-dhcp-client                      \
    mjpg-streamer                        \
    ustreamer                            \
    pdudaemon-client                     \
    sd-mux-ctrl                          \
    ssh                                  \
    sudo                                 \
    systemd-timesyncd                    \
    usbsdmux                             \
    vim                                  \
    wireless-regdb                       \
    wireless-tools                       \
    bluetooth                            \
    python3-libgpiod                     \
    gpiod                                \
"

IMAGE_PREINSTALL:remove:ubuntu-noble = "pdudaemon-client"

# HomeKit support
IMAGE_INSTALL += "python3-hap-python"

# LAVA support
IMAGE_PREINSTALL:append:lava = " lava-dispatcher"

# Expand root file-system
IMAGE_INSTALL:append = " expand-on-first-boot "

# Create a "mtda" user account with "mtda" as the default password
USERS += "mtda"
GROUPS += "mtda"
USER_mtda[gid] = "mtda"
USER_mtda[home] = "/home/mtda"
USER_mtda[comment] = "Multi-Tenant Device Access"
USER_mtda[flags] = "system create-home clear-text-password"
USER_mtda[groups] = "mtda sudo"
USER_mtda[password] ??= "mtda"
USER_mtda[shell] = "/bin/bash"
