#!/bin/bash -e

# If a debian package was created then save it
if [ -f "${ROOTFS_DIR}/root/${BLUEZ_PACKAGE}" ]; then
	cp "${ROOTFS_DIR}/root/${BLUEZ_PACKAGE}" "$DEPLOY_DIR"
fi
