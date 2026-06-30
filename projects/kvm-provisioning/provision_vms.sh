#!/bin/bash

# Ensure the script is run with sufficient privileges
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or use sudo."
  exit 1
fi

# Check if virt-install is installed
if ! command -v virt-install &> /dev/null; then
    echo "virt-install could not be found. Please install it using: sudo apt install virtinst"
    exit 1
fi

echo "========================================"
echo "    VM Provisioning Script (KVM/QEMU)   "
echo "========================================"

# Prompt for the bridge interface
read -p "Enter your bridged network interface name [default: br0]: " BRIDGE_IFACE
BRIDGE_IFACE=${BRIDGE_IFACE:-br0}

# Prompt for Windows 11 ISO
read -p "Enter the full path to the Windows 11 Enterprise ISO: " WIN_ISO
if [ ! -f "$WIN_ISO" ]; then
    echo "Error: Windows 11 ISO file not found at $WIN_ISO"
    exit 1
fi

# Prompt for Ubuntu 26.06 ISO
read -p "Enter the full path to the Ubuntu Server 26.06 ISO: " UBUNTU_ISO
if [ ! -f "$UBUNTU_ISO" ]; then
    echo "Error: Ubuntu ISO file not found at $UBUNTU_ISO"
    exit 1
fi

# Prompt for VirtIO drivers ISO (Required for Windows to recognize virtio disks/networks)
read -p "Enter the full path to the VirtIO drivers ISO (Press Enter to skip if baked in): " VIRTIO_ISO

echo ""
echo "Starting provisioning for Windows 11 Enterprise..."

# Build the Windows virt-install command
WIN_CMD=(
  virt-install
  --name win11-enterprise
  --vcpus 4
  --memory 8192
  --disk size=50,format=qcow2,bus=virtio
  --network bridge="$BRIDGE_IFACE",model=virtio
  --os-variant win11
  --boot uefi
  --features tpm.version=2.0
  --cdrom "$WIN_ISO"
  --noautoconsole
)

# Add VirtIO ISO if provided
if [ -n "$VIRTIO_ISO" ] && [ -f "$VIRTIO_ISO" ]; then
    WIN_CMD+=(--disk "$VIRTIO_ISO",device=cdrom)
fi

# Run the Windows provision command
"${WIN_CMD[@]}"

if [ $? -eq 0 ]; then
    echo "Windows 11 VM provisioning started successfully."
else
    echo "Failed to start Windows 11 VM provisioning."
fi

echo ""
echo "Starting provisioning for Ubuntu Server 26.06..."

# Run the Ubuntu provision command
virt-install \
  --name ubuntu-server-26.06 \
  --vcpus 4 \
  --memory 8192 \
  --disk size=50,format=qcow2,bus=virtio \
  --network bridge="$BRIDGE_IFACE",model=virtio \
  --os-variant ubuntu24.04 \
  --cdrom "$UBUNTU_ISO" \
  --noautoconsole

if [ $? -eq 0 ]; then
    echo "Ubuntu Server VM provisioning started successfully."
else
    echo "Failed to start Ubuntu Server VM provisioning."
fi

echo ""
echo "========================================"
echo "Provisioning commands issued."
echo "You can view the progress and interact with the VMs using 'virt-manager' or 'virsh console'."
