# Setup mtda with a virtual target (based on kvm)

## Getting Started

Copy the sample configuration shipped with the code to `/etc/mtda/config`:

```
sudo install -m 0755 -d /etc/mtda
sudo install -m 0644 configs/qemu.ini /etc/mtda/config
```

Make sure kvm is installed:

```
sudo apt install qemu-kvm
```

The user running the MTDA daemon should be added to the kvm group:

```
sudo addgroup $USER kvm
```

Logout or reboot your PC for the group changes to take effect. You will then
need to start the daemon on your host:

```
mtda-cli -d -n
```

The daemon will create three disk image files on startup if they do not exist
(you may create these files yourself with different sizes):

 * ssd.img: 16 GiB serving as primary storage
 * usb-sdmux.img: 8 GiB as a mass storage that be swapped between host & target
 * usb-data-storage.img: an extra mass storage device

The shared storage (`usb-sdmux`) may be initialized as follows:

```
mtda-cli target off
mtda-cli storage host
mtda-cli storage write my-os-installer.img
```

You may then instruct MTDA to boot from the shared storage drive:

```
mtda-cli storage target
mtda-cli setenv boot-from-usb 1
mtda-cli target on
```

You may use VNC to access the emulated display (port 5900, no user authentication).

## TPM emulation

QEMU may emulate a TPM. The following steps were required for debian-based hosts.

### Add missing tpmtool in gnutls-bin

Make sure your /etc/apt/sources.list files includes deb-src entries (you may
need to uncomment entries created by the Debian/Ubuntu installer) and run apt
update to fetch the deb-src package feeds.

You will then need to pull sources of the gnutls-bin package:

```
apt-get source gnutls-bin
```

Amend debian/control from the gnutls sources to add libtspi-dev to Build-Depends like so:

```
Source: gnutls28
Section: libs
Priority: optional
Maintainer: Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>
XSBC-Original-Maintainer: Debian GnuTLS Maintainers <pkg-gnutls-maint@lists.alioth.debian.org>
Uploaders:
 Andreas Metzler <ametzler@debian.org>,
 Eric Dorland <eric@debian.org>,
 ...
Build-Depends:
 ...
 libssl-dev <!nocheck>,
 libtasn1-6-dev (>= 4.9),
 libtspi-dev,
 libunbound-dev (>= 1.5.10-1),
 libunistring-dev (>= 0.9.7),
 net-tools [!kfreebsd-i386 !kfreebsd-amd64] <!nocheck>,
 ...
```

and replace --without-tpm with --with-tpm in debian/rules:

```
...
CONFIGUREARGS = \
        --enable-ld-version-script --enable-cxx \
        --disable-rpath \
        --enable-libdane --with-tpm \
        --enable-openssl-compatibility \
        --disable-silent-rules \
        ...
```

You will then need to install the build dependencies:

```
sudo mk-build-deps -i -r
```

and build the modified package:

```
dpkg-buildpackage -b -uc -us
```

You may now check if the gnutls-bin package includes the tpmtool:

```
dpkg-deb -c gnutls-bin_*_amd64.deb |grep tpmtool
-rwxr-xr-x root/root    178040 2020-06-15 17:10 ./usr/bin/tpmtool
-rw-r--r-- root/root      2322 2020-06-15 17:10 ./usr/share/man/man1/tpmtool.1.gz
```

and install the updated packages:

```
sudo dpkg -i gnutls-bin_*_amd64.deb libgnutls-dane0_*_amd64.deb libgnutls30_*_amd64.deb
(Reading database ... 81477 files and directories currently installed.)
Preparing to unpack gnutls-bin_3.6.13-2ubuntu1.2_amd64.deb ...
Unpacking gnutls-bin (3.6.13-2ubuntu1.2) over (3.6.13-2ubuntu1.2) ...
Preparing to unpack libgnutls-dane0_3.6.13-2ubuntu1.2_amd64.deb ...
Unpacking libgnutls-dane0:amd64 (3.6.13-2ubuntu1.2) over (3.6.13-2ubuntu1.2) ...
Preparing to unpack libgnutls30_3.6.13-2ubuntu1.2_amd64.deb ...
Unpacking libgnutls30:amd64 (3.6.13-2ubuntu1.2) over (3.6.13-2ubuntu1) ...
Setting up libgnutls30:amd64 (3.6.13-2ubuntu1.2) ...
Setting up libgnutls-dane0:amd64 (3.6.13-2ubuntu1.2) ...
Setting up gnutls-bin (3.6.13-2ubuntu1.2) ...
Processing triggers for man-db (2.9.1-1) ...
Processing triggers for libc-bin (2.31-0ubuntu9) ...
```

### Get and build libtpms

Fetch the latest release from GitHub:

```
git clone https://github.com/stefanberger/libtpms.git
cd libtpms
git checkout v0.7.3
```

and build it as follows:

```
sudo mk-build-deps -i -r
dpkg-buildpackage -b -uc -us
```

and install it:

```
cd ..
sudo dpkg -i libtpms-dev_*_amd64.deb libtpms0_*_amd64.deb
```

### Get and build swtpm

Fetch the latest release from GitHub:

```
git clone https://github.com/stefanberger/swtpm.git
cd swtpm
git checkout v0.3.4
```

and build it as follows:

```
sudo mk-build-deps -i -r
dpkg-buildpackage -b -uc -us
```

and install it:

```
cd ..
sudo dpkg -i swtpm_*_amd64.deb swtpm-libs_*_amd64.deb
```
