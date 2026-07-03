<!-- AUTO-GENERATED MERMAID START -->
<!-- This Mermaid diagram is auto-generated. Do not edit directly. -->

## Directory structure

<details>
<summary>Show GitGraph diagram for `scripts-public`</summary>

```mermaid
gitGraph
    commit id: "root: scripts-public"
    commit id: "dir: .agents (2 entries)"
    commit id: "file: .gitattributes (170 bytes)"
    commit id: "file: .gitignore (256 bytes)"
    commit id: "dir: bash (7 entries)"
    commit id: "dir: markdown (1 entries)"
    commit id: "dir: markup (2 entries)"
    commit id: "dir: PowerShell (1 entries)"
    commit id: "dir: powershell (6 entries)"
    commit id: "dir: projects (4 entries)"
    commit id: "dir: python (6 entries)"
    commit id: "file: README.md (6640 bytes)"
    commit id: "file: SECURITY.md (221 bytes)"
    commit id: "dir: web (2 entries)"
    commit id: "dir: wordpress (20 entries)"
```

</details>

<!-- AUTO-GENERATED MERMAID END -->

# Public Scripts (`scripts-public`)

A curated collection of utility scripts, automation tools, and applications for various environments.

All of these scripts along with detailed writeups on their usage and configuration can be found on my WordPress blog: [Extreme Sarcasm](https://extremesarcasm.org).


The [scripts_catalog.md](wordpress/scripts_catalog.md) in this repository was generated using [Google Antigravity](https://antigravity.google/).

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
├── powershell/         # Windows PowerShell utility scripts
├── python/             # Python-based tools and CLI programs
├── projects/           # Various complete projects and scripts
├── web/                # Web configuration utilities and server scripts
└── wordpress/          # WordPress blog posts, catalogs, and guides
```

---

## Catalog of Tools

### 🐚 Linux Bash (`/bash`)
* [apache-proxy-wizard.sh](bash/apache-proxy-wizard.sh): An interactive bash wizard for configuring Apache reverse proxy setups with manual SSL or automated Let's Encrypt integration.
* [openssl-certtool.sh](bash/openssl-certtool.sh): A bash script for generating and managing OpenSSL certificates.
* [script-public-merge.sh](bash/script-public-merge.sh): A utility script to merge public scripts into a repository.
* [user_manager.sh](bash/user_manager.sh): Menu-driven Linux user account manager for Ubuntu.

### 🔷 Windows PowerShell (`/powershell`)
* [Calculate-FolderStats.ps1](powershell/Calculate-FolderStats.ps1): Recursively calculates and reports total files, folders, and sizes in a directory.
* [check_mtu.ps1](powershell/check_mtu.ps1): Checks and reports the Maximum Transmission Unit (MTU) size for network interfaces.
* [openssl-certtool.ps1](powershell/openssl-certtool.ps1): A PowerShell utility to extract certificates, CA chains, private keys, PEM bundles, and CSRs.
* [Create-RecoveryPartition.ps1](powershell/recovery-partition/Create-RecoveryPartition.ps1): Automates shrinking the C: drive and creating a Windows recovery partition.
* [Create-RecoveryPartition2.ps1](powershell/recovery-partition/Create-RecoveryPartition2.ps1): Alternative script for detecting and configuring a Windows recovery partition.
* [Create-RecoveryPartition3.ps1](powershell/recovery-partition/Create-RecoveryPartition3.ps1): Advanced script for disabling current mappings and creating a new recovery environment.
* [RecoveryPartitionManager.ps1](powershell/recovery-partition/RecoveryPartitionManager.ps1): A comprehensive menu-driven utility for managing Windows recovery partitions.
* [Remove-RecoveryPartition.ps1](powershell/recovery-partition/Remove-RecoveryPartition.ps1): Automates the safe detection and removal of a Windows recovery partition.


### 📝 WordPress Blog Posts (`/wordpress`)
* [about.md](wordpress/about.md): The About page biography from Extreme Sarcasm.
* [antigravity_blog_post.md](wordpress/antigravity_blog_post.md): A comprehensive guide on Google Antigravity and generating PowerShell scripts.
* [mermaid-markup-language-guide.md](wordpress/mermaid-markup-language-guide.md): A complete guide to using Mermaid JS in VS Code.
* [aws-ec2-antigravity-blog.md](wordpress/aws-ec2-antigravity-blog.md): A sarcastic, humorous guide on provisioning an AWS EC2 instance for Google Antigravity.
* [how-to-update-rust-desk-pro-self-hosted-docker.md](wordpress/how-to-update-rust-desk-pro-self-hosted-docker.md): A guide on how to update Rust Desk Pro Self Hosted using Docker.
* [technical-writing.md](wordpress/technical-writing.md): A markdown rewrite of the Technical Writing page from Extreme Sarcasm.
* [ultimate-guide-to-bitwarden-securing-your-digital-life-across-every-device.md](wordpress/ultimate-guide-to-bitwarden-securing-your-digital-life-across-every-device.md): Ultimate Guide to Bitwarden: Securing Your Digital Life Across Every Device.

### 📊 Mermaid JS Examples (`/wordpress/mermaid-examples`)
* [flowchart.md](wordpress/mermaid-examples/flowchart.md): An example of a basic user registration flowchart.
* [gantt.md](wordpress/mermaid-examples/gantt.md): An example of a software development sprint Gantt chart.
* [sequence.md](wordpress/mermaid-examples/sequence.md): An example of an OAuth authentication sequence diagram.
* [state.md](wordpress/mermaid-examples/state.md): An example of an e-commerce shopping cart state diagram.

### 📁 Projects (`/projects`)
* [provision_vms.sh](projects/kvm-provisioning/provision_vms.sh): A bash script to automatically provision Windows 11 and Ubuntu VMs using virt-install (KVM/QEMU).
* [client.py](projects/stftp/client.py): A Python client script implementing STFTP (Simple Trivial File Transfer Protocol).
* [client2.py](projects/stftp/client2.py): An alternative Python STFTP client with modified configuration options.
* [server.py](projects/stftp/server.py): A Python STFTP server script to receive and store incoming files.
* [server2.py](projects/stftp/server2.py): An alternative Python STFTP server with modified configuration options.

---

## ⚠️ Disclaimer

Running executable scripts from the internet without checking the contents is generally a bad idea. Please inspect any code prior to execution. See our [Disclaimer & Terms of Use](file:///home/rtroiano/scripts-public/scripts-public/web/apache-reverse-proxy/disclaimer.html) for more details.
