# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

IMAGE_INSTALL += "    \
    mtda              \
    sshd-regen-keys   \
"

IMAGE_PREINSTALL += " \
    iproute2          \
    isc-dhcp-client   \
    network-manager   \
    ssh               \
    vim               \
"

# Create a "mtda" user account with "mtda" as the default password
# hash created with: python3 -c 'import crypt; print(crypt.crypt("mtda", crypt.mksalt(crypt.METHOD_SHA512)))'
USERS += "mtda"
GROUPS += "mtda"
USER_mtda[gid] = "mtda"
USER_mtda[home] = "/home/mtda"
USER_mtda[comment] = "Mentor Test Device Agent"
USER_mtda[flags] = "system create-home"
USER_mtda[password] ??= "$6$uaP1WXXu/joK8zxJ$LONexagmcWBKkY/HRQe0fVjY7n06FkX1qJUjigQ.4JVYxC9/OfBu3iJrF8hugMo2CaIh1sIOxDdpXvWWIjhfQ1"

# Remove the "isar" account
USERS_remove = "isar"
