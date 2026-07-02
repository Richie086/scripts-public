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
* [apache-proxy-wizard.sh](bash/apache-proxy-wizard.sh): An interactive bash wizard for generating and configuring Apache reverse proxy setups.
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


### 🧪 Testing & Directory Analysis (`/testing`)
* [dir_stats.sh](testing/dir_stats.sh): A bash script that analyzes and reports detailed directory statistics.
* [update_readme.py](testing/update_readme.py): A Python script that automates the generation and updating of the README.md file.

### 📝 WordPress Blog Posts (`/wordpress`)
* [antigravity_blog_post.md](wordpress/antigravity_blog_post.md): A comprehensive guide on Google Antigravity and generating PowerShell scripts.
* [mermaid-markup-language-guide.md](wordpress/mermaid-markup-language-guide.md): A complete guide to using Mermaid JS in VS Code.
* [aws-ec2-antigravity-blog.md](wordpress/aws-ec2-antigravity-blog.md): A sarcastic, humorous guide on provisioning an AWS EC2 instance for Google Antigravity.
* [how-to-update-rust-desk-pro-self-hosted-docker.md](wordpress/how-to-update-rust-desk-pro-self-hosted-docker.md): A guide on how to update Rust Desk Pro Self Hosted using Docker.
* [technical-writing.md](wordpress/technical-writing.md): A markdown rewrite of the Technical Writing page from Extreme Sarcasm.

### 📊 Mermaid JS Examples (`/markdown/mermaid-examples`)
* [flowchart.md](markdown/mermaid-examples/flowchart.md): An example of a basic user registration flowchart.
* [gantt.md](markdown/mermaid-examples/gantt.md): An example of a software development sprint Gantt chart.
* [sequence.md](markdown/mermaid-examples/sequence.md): An example of an OAuth authentication sequence diagram.
* [state.md](markdown/mermaid-examples/state.md): An example of an e-commerce shopping cart state diagram.

### 📁 Projects (`/projects`)
* [provision_vms.sh](projects/kvm-provisioning/provision_vms.sh): A bash script to automatically provision Windows 11 and Ubuntu VMs using virt-install (KVM/QEMU).
* [client.py](projects/stftp/client.py): A Python client script implementing STFTP (Simple Trivial File Transfer Protocol).
* [client2.py](projects/stftp/client2.py): An alternative Python STFTP client with modified configuration options.
* [server.py](projects/stftp/server.py): A Python STFTP server script to receive and store incoming files.
* [server2.py](projects/stftp/server2.py): An alternative Python STFTP server with modified configuration options.

---

## ⚠️ Disclaimer

Running executable scripts from the internet without checking the contents is generally a bad idea. Please inspect any code prior to execution. See our [Disclaimer & Terms of Use](file:///home/rtroiano/scripts-public/scripts-public/web/apache-reverse-proxy/disclaimer.html) for more details.
