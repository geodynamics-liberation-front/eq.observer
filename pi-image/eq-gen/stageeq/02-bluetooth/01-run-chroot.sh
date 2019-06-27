#!/bin/bash -e

echo BLUEZ_PACKAGE=$BLUEZ_PACKAGE
echo BLUEZ_URL=$BLUEZ_URL
echo BLUEZ_TAR=$BLUEZ_TAR
echo BLUEZ_DIR=$BLUEZ_DIR

# Check for an existing debian package
if [ -f "/root/${BLUEZ_PACKAGE}" ]; then
	dpkg  -i "/root/${BLUEZ_PACKAGE}" 
	# Remove so it doesn't get put in the deploy
	rm "/root/${BLUEZ_PACKAGE}"
else
	# We run apt commands because we are going to uninstall later and ##-packages doesn't support remove
	apt install --no-install-recommends -y libusb-dev libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev checkinstall
	# Prepare the directory, build in /root/src
	cd /root
	mkdir -p src
	cd src
	# get the bluez tarball
	wget -O ${BLUEZ_TAR} ${BLUEZ_URL}
	tar -xvf ${BLUEZ_TAR}
	BLUEZ_DIR=$(tar -tvf ${BLUEZ_TAR} | grep "/$" | tr -s " " | cut -d " " -f 6 | grep -v "/.*/")
	cd ${BLUEZ_DIR}
	./configure
	make
	# Use checkinstall to create a package
	checkinstall -y --fstrans=no --maintainer=eq@eq.observer
	# cleanup the packages only needed for the buiild
	apt remove -y libusb-dev libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev checkinstall
#	apt autoremove -y
	# save the deb package
	cd /root
	mv src/${BLUEZ_DIR}/${BLUEZ_PACKAGE} .
#	rm -rf src
fi
