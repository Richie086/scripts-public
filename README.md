# Public Scripts (`scripts-public`)

A curated collection of utility scripts, automation tools, and applications for various environments.

The [scripts_catalog.md](scripts_catalog.md) in this repository was generated using [Google Antigravity](https://antigravity.google/).

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
└── web/                # Web configuration utilities and server scripts
```

---

## Catalog of Tools

### 🐚 Linux Bash (`/bash`)
* [openssl-certtool.sh](file:///home/rtroiano/scripts-public/scripts-public/bash/openssl-certtool.sh): Interactive shell script for generating, converting, and analyzing OpenSSL certificates.
* [script-public-merge.sh](file:///home/rtroiano/scripts-public/scripts-public/bash/script-public-merge.sh): Helper script for merging codebase resources.

### 🔷 Windows PowerShell (`/powershell`)
* [openssl-certtool.ps1](file:///home/rtroiano/scripts-public/scripts-public/powershell/openssl-certtool.ps1): Interactive Windows PowerShell equivalent of the OpenSSL certificate utility.
* [check_mtu.ps1](file:///home/rtroiano/scripts-public/scripts-public/powershell/check_mtu.ps1): Utility for diagnosing Maximum Transmission Unit (MTU) sizes.
* [recovery-partition/](file:///home/rtroiano/scripts-public/scripts-public/powershell/recovery-partition/): Suite of scripts to automate creating, removing, and managing Windows Recovery Partitions.

### 🐍 Python (`/python`)
* [stftp/](file:///home/rtroiano/scripts-public/scripts-public/python/stftp/): Python-based client-server implementation of the Secure Trivial File Transfer Protocol.

### 🌐 Web / Server Config (`/web`)
* [apache-reverse-proxy/](file:///home/rtroiano/scripts-public/scripts-public/web/apache-reverse-proxy/): Interactive configuration generation wizard for Apache reverse proxy setups.

---

## ⚠️ Disclaimer

Running executable scripts from the internet without checking the contents is generally a bad idea. Please inspect any code prior to execution. See our [Disclaimer & Terms of Use](file:///home/rtroiano/scripts-public/scripts-public/web/apache-reverse-proxy/disclaimer.html) for more details.
