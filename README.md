# Public Scripts (`scripts-public`)

A curated collection of utility scripts, automation tools, and applications for various environments.

All of these scripts along with detailed writeups on their usage and configuration can be found on my WordPress blog: [Extreme Sarcasm](https://extremesarcasm.org).


The [scripts_catalog.md](markdown/scripts_catalog.md) in this repository was generated using [Google Antigravity](https://antigravity.google/).

For more information about Google Antigravity, check out the [Official Documentation](https://antigravity.google/docs) or download the platform for your operating system:
* 🪟 [Windows Download](https://antigravity.google/download/windows)
* 🍎 [macOS Download](https://antigravity.google/download/macos)
* 🐧 [Linux Download](https://antigravity.google/download/linux)


## Repository Structure

The repository is organized by environment and runtime type:

```text
scripts-public/
├── .agents/            # Workspace agent rules and guidelines
├── bash/               # Linux Bash utility scripts
├── markdown/           # WordPress blog posts and writeups
├── powershell/         # Windows PowerShell utility scripts
├── python/             # Python-based tools and CLI programs
├── projects/           # Various complete projects and scripts
├── testing/            # Directory analysis testing scripts
├── web/                # Web configuration utilities and server scripts
└── wordpress/          # WordPress blog posts and guides
```

---

## Catalog of Tools

### 🐚 Linux Bash (`/bash`)
* [openssl-certtool.sh](bash/openssl-certtool.sh): 1. Initialization & Security Setup Color codes for readable output
* [script-public-merge.sh](bash/script-public-merge.sh): Ensure we are in the root of the existing repo

### 🔷 Windows PowerShell (`/powershell`)
* [Calculate-FolderStats.ps1](powershell/Calculate-FolderStats.ps1): Recursively calculates and reports total files, folders, and sizes in a directory.
* [check_mtu.ps1](powershell/check_mtu.ps1): ----------------------------- HELP / USAGE
* [openssl-certtool.ps1](powershell/openssl-certtool.ps1): Extract certificates, CA chains, private keys, PEM bundles, and CSRs from
* [Create-RecoveryPartition.ps1](powershell/recovery-partition/Create-RecoveryPartition.ps1): PHASE 1: SHRINK C: AND CREATE THE PARTITION
* [Create-RecoveryPartition2.ps1](powershell/recovery-partition/Create-RecoveryPartition2.ps1): 1. Automatically detect the volume labeled "Recovery" on your main system disk
* [Create-RecoveryPartition3.ps1](powershell/recovery-partition/Create-RecoveryPartition3.ps1): 1. Turn off the current Recovery Environment mapping to avoid conflicts
* [RecoveryPartitionManager.ps1](powershell/recovery-partition/RecoveryPartitionManager.ps1): Requires Administrator Privileges
* [Remove-RecoveryPartition.ps1](powershell/recovery-partition/Remove-RecoveryPartition.ps1): 1. Automatically find the C: Drive disk and partition details

### 🐍 Python (`/python`)
* [client.py](python/stftp/client.py): --- Protocol Framing Logic ---
* [client2.py](python/stftp/client2.py): --- Client Configuration ---
* [server.py](python/stftp/server.py): Define the master folder where all incoming files will be trapped
* [server2.py](python/stftp/server2.py): --- Server Configuration ---

### 🧪 Testing & Directory Analysis (`/testing`)
* [dir_stats.sh](testing/dir_stats.sh): Target directory to analyze (default: current directory)
* [update_readme.py](testing/update_readme.py): !/usr/bin/env python3

### 📝 WordPress Blog Posts (`/wordpress`)
* [antigravity_blog_post.md](wordpress/antigravity_blog_post.md): A comprehensive guide on Google Antigravity and generating PowerShell scripts.
* [aws-ec2-antigravity-blog.md](wordpress/aws-ec2-antigravity-blog.md): A sarcastic, humorous guide on provisioning an AWS EC2 instance for Google Antigravity.

### 🌐 Web / Server Config (`/web`)
* [apache-proxy-wizard.sh](web/apache-reverse-proxy/apache-proxy-wizard.sh): COLOR DEFINITIONS

### 📁 Projects (`/projects`)
* [provision_vms.sh](projects/kvm-provisioning/provision_vms.sh): A bash script to automatically provision Windows 11 and Ubuntu VMs using virt-install (KVM/QEMU).

---

## ⚠️ Disclaimer

Running executable scripts from the internet without checking the contents is generally a bad idea. Please inspect any code prior to execution. See our [Disclaimer & Terms of Use](file:///home/rtroiano/scripts-public/scripts-public/web/apache-reverse-proxy/disclaimer.html) for more details.
