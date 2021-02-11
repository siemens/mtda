# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

# Default device/file to use for our USB Mass Storage Gadget
MTDA_MASS_STORAGE_FILE ??= "mmcblk0"

# MTDA Package Feeds
MTDA_APT_URI ??= "https://dl.bintray.com/chombourger/mtda"

# Build and deploy our MTDA packages
DEPENDS += "mtda-packages"
do_build[deptask] += "do_deploy_deb"

IMAGE_INSTALL += "                       \
    mtda-hostname                        \
    sshd-regen-keys                      \
    usb-ms-use-${MTDA_MASS_STORAGE_FILE} \
"

IMAGE_PREINSTALL += "                    \
    iproute2                             \
    isc-dhcp-client                      \
    lavapdu-client                       \
    mtda                                 \
    mtda-usb-functions                   \
    network-manager                      \
    sd-mux-ctrl                          \
    ssh                                  \
    sudo                                 \
    vim                                  \
"

# HomeKit support
IMAGE_PREINSTALL += "python3-hap-python"

# LAVA support
IMAGE_PREINSTALL += "lava-dispatcher"

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
USER_mtda[comment] = "Multi-Tenant Device Access"
USER_mtda[flags] = "system create-home"
USER_mtda[groups] = "mtda sudo"
USER_mtda[password] ??= "$6$uaP1WXXu/joK8zxJ$LONexagmcWBKkY/HRQe0fVjY7n06FkX1qJUjigQ.4JVYxC9/OfBu3iJrF8hugMo2CaIh1sIOxDdpXvWWIjhfQ1"
USER_mtda[shell] = "/bin/bash"

# Remove the "isar" accounts
GROUPS_remove = "isar"
USERS_remove  = "isar"

# Add mtda package feeds to /etc/apt/sources.list.d/
ROOTFS_POSTPROCESS_COMMAND += "mtda_add_apt_sources"
mtda_add_apt_sources() {
    echo "deb [trusted=yes] ${MTDA_APT_URI} ${BASE_DISTRO_CODENAME} main" \
        | sudo tee -a ${IMAGE_ROOTFS}/etc/apt/sources.list.d/mtda.list
}
