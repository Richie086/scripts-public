#!/usr/bin/env bash
# Script Name: setup_shared_dev_server.sh
# Description: Configures a shared Linux development server for multiple developers.
#              Sets up the shared devs group, shared directory with SetGID, and 
#              appropriate Access Control Lists (ACLs).
#
# Standards: set -euo pipefail is active. No hardcoded local IPs or credentials.

set -euo pipefail

# Environment variables with sensible defaults
DEV_GROUP="${DEV_GROUP:-devs}"
SHARED_DIR="${SHARED_DIR:-/srv/projects}"

echo "============================================="
echo "Shared Development Server Environment Setup"
echo "Group:      ${DEV_GROUP}"
echo "Directory:  ${SHARED_DIR}"
echo "============================================="

# 1. Ensure the devs group exists
if ! getent group "${DEV_GROUP}" >/dev/null; then
    echo "Creating group '${DEV_GROUP}'..."
    sudo groupadd "${DEV_GROUP}"
else
    echo "Group '${DEV_GROUP}' already exists."
fi

# 2. Setup the shared projects directory
echo "Creating shared directory at ${SHARED_DIR}..."
sudo mkdir -p "${SHARED_DIR}"

# 3. Apply group ownership
echo "Applying group ownership to ${SHARED_DIR}..."
sudo chown -R root:${DEV_GROUP} "${SHARED_DIR}"
sudo chmod -R 775 "${SHARED_DIR}"

# 4. Set SETGID bit
# This ensures that any new files/folders created inside have group 'devs'
echo "Enabling SETGID on ${SHARED_DIR}..."
sudo chmod g+s "${SHARED_DIR}"

# 5. Apply default Access Control Lists (ACLs)
# This guarantees that files created by one developer can be written by another
if command -v setfacl >/dev/null; then
    echo "Configuring ACLs..."
    sudo setfacl -R -d -m g:${DEV_GROUP}:rwx "${SHARED_DIR}"
    sudo setfacl -R -m g:${DEV_GROUP}:rwx "${SHARED_DIR}"
else
    echo "WARNING: 'acl' package not found. Installing now..."
    sudo apt-get update && sudo apt-get install -y acl
    sudo setfacl -R -d -m g:${DEV_GROUP}:rwx "${SHARED_DIR}"
    sudo setfacl -R -m g:${DEV_GROUP}:rwx "${SHARED_DIR}"
fi

echo "============================================="
echo "Setup Complete!"
echo "To add a developer to the group:"
echo "  sudo usermod -aG ${DEV_GROUP} <username>"
echo ""
echo "Note: Developers must log out and back in for group changes to take effect."
echo "============================================="
