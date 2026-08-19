# VirtualBox Guest Additions Setup & Configuration Script

Unified automation script to install VirtualBox Guest Additions (`virtualbox-guest-dkms` and `virtualbox-guest-x11`) and configure bidirectional clipboard / drag-and-drop support.

## Overview

The script supports two execution modes based on where you trigger it:

1. **Inside the Guest VM**:
   - Updates local package indexes.
   - Installs VirtualBox kernel modules and X11 display integration via `apt-get`.
   - Offers an immediate reboot prompt.

2. **On the Host Machine (Controlled via SSH)**:
   - Connects to the target VM over SSH to trigger package updates and installation.
   - Uses local `VBoxManage` on the host to set `--clipboard bidirectional` and `--draganddrop bidirectional`.
   - Issues a graceful reboot to the remote target VM.

## Usage

```bash
# Make script executable
chmod +x virtualbox-install-guest-addtions-enable-bidrectional-clipboard.sh

# Run the interactive setup script
./virtualbox-install-guest-addtions-enable-bidrectional-clipboard.sh
```
