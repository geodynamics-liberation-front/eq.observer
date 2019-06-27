#!/bin/bash -e

echo BLUEZ_PACKAGE=$BLUEZ_PACKAGE
echo BLUEZ_URL=$BLUEZ_URL
echo BLUEZ_TAR=$BLUEZ_TAR
echo BLUEZ_DIR=$BLUEZ_DIR

if [ -f files/$BLUEZ_PACKAGE ]; then
	install -m 644 "files/${BLUEZ_PACKAGE}" "${ROOTFS_DIR}/root/${BLUEZ_PACKAGE}"
fi
