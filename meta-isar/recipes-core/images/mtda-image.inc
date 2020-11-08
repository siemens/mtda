# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

# Default device/file to use for our USB Mass Storage Gadget
MTDA_MASS_STORAGE_FILE ??= "mmcblk0"

# Make sure packages we build are deployed
do_build[deptask] += "do_deploy_deb"

# Here's our list of custom packages
MTDA_PACKAGES = "                        \
    mtda                                 \
    mtda-hostname                        \
    mtda-usb-functions                   \
    sd-mux-ctrl                          \
    sshd-regen-keys                      \
    usb-ms-use-${MTDA_MASS_STORAGE_FILE} \
"
DEPENDS += " ${MTDA_PACKAGES} "

# and to the image...
IMAGE_PREINSTALL += "${MTDA_PACKAGES}"

# HAP-python requires a few more custom packages, list them here
HAP_PACKAGES = "     \
    hap-python       \
"
DEPENDS += " ${HAP_PACKAGES} "

HAP_PREINSTALL = "     \
    python3-hap-python \
"

LAVA_PREINSTALL = " \
    lava-dispatcher \
"

# Finally, add the following Debian packages to the image
IMAGE_PREINSTALL += "  \
    ${HAP_PREINSTALL}  \
    ${LAVA_PREINSTALL} \
    iproute2           \
    isc-dhcp-client    \
    network-manager    \
    ssh                \
    sudo               \
    vim                \
"

# Expand root file-system
IMAGE_INSTALL_append = " expand-on-first-boot "

# Remove meta-isar examples if they are there...
IMAGE_INSTALL_remove = "          \
    example-module-${KERNEL_NAME} \
    example-raw                   \
    hello-isar                    \
    samefile                      \
"

# Create a "mtda" user account with "mtda" as the default password
# hash created with: python3 -c 'import crypt; print(crypt.crypt("mtda", crypt.mksalt(crypt.METHOD_SHA512)))'
USERS += "mtda"
GROUPS += "mtda"
USER_mtda[gid] = "mtda"
USER_mtda[home] = "/home/mtda"
USER_mtda[comment] = "Mentor Test Device Agent"
USER_mtda[flags] = "system create-home"
USER_mtda[groups] = "mtda sudo"
USER_mtda[password] ??= "$6$uaP1WXXu/joK8zxJ$LONexagmcWBKkY/HRQe0fVjY7n06FkX1qJUjigQ.4JVYxC9/OfBu3iJrF8hugMo2CaIh1sIOxDdpXvWWIjhfQ1"
USER_mtda[shell] = "/bin/bash"

# Remove the "isar" accounts
GROUPS_remove = "isar"
USERS_remove  = "isar"
