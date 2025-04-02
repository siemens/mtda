# ---------------------------------------------------------------------------
# This OpenEmbedded Kickstart file is part of MTDA
# Copyright (C) 2025 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# EFI partition containing efibootguard bootloader binary
part --source efibootguard-efi  --fixed-size 128M --label efi   --align 1024 --part-type=EF00 --active --fsuuid 0x2321dcba --uuid 45c5347d-a0d9-42a8-a36a-1ce2768e99ce

# EFI Boot Guard environment/config partitions plus Kernel files
part --source efibootguard-boot --fixed-size 256M --label BOOT0 --align 1024 --part-type=0700 --sourceparams "revision=2" --fsuuid 0x4321dcbb --uuid e8567692-2dfa-459a-be15-f6e5ddcc8f49
part --source efibootguard-boot --fixed-size 256M --label BOOT1 --align 1024 --part-type=0700 --sourceparams "revision=1" --fsuuid 0x4321dcbc --uuid 94b2174d-c792-4e8e-8a34-b506e2927937
