#!/bin/bash

# ====================================================================
# UNIFIED VIRTUALBOX GUEST ADDITIONS AUTOMATION SCRIPT
# ====================================================================

echo "=================================================================="
echo "    VirtualBox Guest Additions Setup & Configuration"
echo "=================================================================="

# Prompt user for their current environment context
echo "Where are you currently executing this script?"
echo "1) Inside the GUEST VM (Local Ubuntu Virtual Machine)"
echo "2) On the HOST machine (Controlling a Remote VM via SSH)"
echo "=================================================================="
read -p "Enter choice [1 or 2]: " env_choice

# --------------------------------------------------------------------
# CASE 1: EXECUTION RUNNING DIRECTLY INSIDE THE GUEST VM
# --------------------------------------------------------------------
if [ "$env_choice" -eq 1 ]; then
    echo ""
    echo "[*] Initializing local installation inside Guest VM..."
    
    # Ensure local execution has root/sudo privileges
    if [ "$EUID" -ne 0 ]; then
        echo "[!] This script must be run with sudo privileges inside the guest."
        echo "Please re-run using: sudo $0"
        exit 1
    fi

    echo "[*] Updating local package databases..."
    apt-get update
    
    echo "[*] Pulling down and compiling VirtualBox utilities via apt..."
    apt-get install -y virtualbox-guest-dkms virtualbox-guest-x11

    echo "=================================================================="
    echo "[✓] Local installation complete!"
    echo "[!] IMPORTANT: You must still configure Bidirectional Clipboard"
    echo "    manually in the VirtualBox Manager settings on your host machine."
    echo "=================================================================="
    
    read -p "Reboot VM now to apply system changes? (y/n): " reboot_choice
    if [[ "$reboot_choice" =~ ^[Yy]$ ]]; then
        reboot
    fi

# --------------------------------------------------------------------
# CASE 2: EXECUTION RUNNING ON THE HOST MACHINE
# --------------------------------------------------------------------
elif [ "$env_choice" -eq 2 ]; then
    echo ""
    echo "[*] Initializing host-to-guest automation pipeline..."
    
    # Gather remote target details from user input
    read -p "Enter the target VM Name (as shown in VirtualBox): " VM_NAME
    read -p "Enter the SSH username for the Target VM: " VM_USER
    read -p "Enter the IP address or FQDN of the Target VM: " VM_TARGET

    # Verify VBoxManage exists locally on the host before trying to configure hardware
    if ! command -v vboxmanage &> /dev/null; then
        echo "[!] Error: 'vboxmanage' command utility not found on this host system."
        exit 1
    fi

    echo "------------------------------------------------------------------"
    echo "[*] Connecting to remote machine via SSH to deploy packages..."
    ssh -t "${VM_USER}@${VM_TARGET}" "sudo sh -c '
        echo \"=== Inside VM: Updating package tree ===\"
        apt-get update
        echo \"=== Inside VM: Automatically installing Guest Additions suite ===\"
        apt-get install -y virtualbox-guest-dkms virtualbox-guest-x11
    '"

    echo "------------------------------------------------------------------"
    echo "[*] Modifying hardware rules locally via Host VBoxManage..."
    vboxmanage controlvm "$VM_NAME" clipboard bidirectional 2>/dev/null
    vboxmanage controlvm "$VM_NAME" draganddrop bidirectional 2>/dev/null
    vboxmanage modifyvm "$VM_NAME" --clipboard bidirectional 2>/dev/null
    vboxmanage modifyvm "$VM_NAME" --draganddrop bidirectional 2>/dev/null

    echo "------------------------------------------------------------------"
    echo "[*] Issuing a graceful hardware restart instruction to the Guest..."
    ssh "${VM_USER}@${VM_TARGET}" "sudo reboot"

    echo "=================================================================="
    echo "[✓] Pipeline execution finished completely!"
    echo "[✓] Guest is rebooting with bidirectional clipboard enabled natively."
    echo "=================================================================="

else
    echo "[!] Invalid input selection. Aborting execution parameters."
    exit 1
fi
