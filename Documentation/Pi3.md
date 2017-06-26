
# Setup of a Raspberry Pi3 as a MTDA agent

The Raspberry Pi3 is a cheap ARM-based board with great connectivity (USB, Ethernet,
Wi-Fi, Bluetooth) and is a nice platform to run MTDA as a server on your network.

## Install Ubuntu MATE

Download and install Ubuntu MATE from the following location:

   * https://goo.gl/w2Tiq9

The SHA256 checksum of this image is:

   * dc3afcad68a5de3ba683dc30d2093a3b5b3cd6b2c16c0b5de8d50fede78f75c2

Uncompress and burn this image to a microSD card (8GB or larger). Insert the microSD
card into the Raspberry Pi3 and follow the on-screen instructions (you will need to
attach a USB keyboard and mouse to the Pi3 as well as an HDMI display).

Note that on the first boot (after the inital setup), this image will loose Wi-Fi
connectivity. Simply restart your device to get it back up.

## Install sd-mux-ctrl

If you have a Samsung SD-Mux device (or a derivative), you will want to install the
sd-mux-ctrl tool. You first need to install some development packages to the system:

```
sudo apt-get -y install build-essential cmake git libpopt-dev libftdi1-dev
```

You then need to grab the sd-mux project source code with:

```
git clone git://git.tizen.org/tools/testlab/sd-mux
```

and build it as follows:

```
cd sd-mux
vi src/main.c
# look for the parseArguments function, and make the "c" variable a "signed char"
# instead of "char" (the build would otherwise fail since built with -Werror)
mkdir build
cd build
cmake ..
make
sudo make install
```

## Install MTDA

```
sudo apt-get install \
   python3-daemon python3-dev python3-serial \
   python3-setuptools python3-usb python3-zmq
```

The setup script should then be used to install command-line scripts and packages:

```
sudo python3 setup.py install
```
