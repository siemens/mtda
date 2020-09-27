# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

# Default device/file to use for our USB Mass Storage Gadget
MTDA_MASS_STORAGE_FILE ??= "mmcblk0"

# Here's our list of custom packages
MTDA_PACKAGES = "                        \
    mtda                                 \
    mtda-hostname                        \
    mtda-usb-functions                   \
    sd-mux-ctrl                          \
    sshd-regen-keys                      \
    usb-ms-use-${MTDA_MASS_STORAGE_FILE} \
"

# Add them as build dependencies
DEPENDS += " ${MTDA_PACKAGES} "

# And now add them to the image
IMAGE_PREINSTALL += "${MTDA_PACKAGES}"

# Finally, add the following Debian packages to the image
IMAGE_PREINSTALL += "  \
    iproute2           \
    isc-dhcp-client    \
    network-manager    \
    ssh                \
    sudo               \
    vim                \
"

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
USER_mtda[comment] = "Multi-Tenant Device Access"
USER_mtda[flags] = "system create-home"
USER_mtda[groups] = "mtda sudo"
USER_mtda[password] ??= "$6$uaP1WXXu/joK8zxJ$LONexagmcWBKkY/HRQe0fVjY7n06FkX1qJUjigQ.4JVYxC9/OfBu3iJrF8hugMo2CaIh1sIOxDdpXvWWIjhfQ1"

# Remove the "isar" accounts
GROUPS_remove = "isar"
USERS_remove  = "isar"
