# Workspace Catalog: `scripts-public`

Welcome to the **scripts-public** interactive folder browser. This catalog provides an overview, quick-access links, and detailed functional descriptions of the automation utilities, network tools, and configuration wizards available in this workspace.

---

## 📁 Repository Architecture

```mermaid
graph TD
    root["scripts-public (Root)"] --> agents["⚙️ .agents/"]
    root --> bash["🐚 bash/"]
    root --> powershell["🔷 powershell/"]
    root --> python["🐍 python/"]
    root --> testing["🧪 testing/"]
    root --> web["🌐 web/"]
    root --> dir_stats_report["directory_stats.md"]

    agents --> agents_md["AGENTS.md"]
    bash --> cert_sh["openssl-certtool.sh"]
    bash --> merge_sh["script-public-merge.sh"]

    powershell --> check_mtu["check_mtu.ps1"]
    powershell --> cert_ps1["openssl-certtool.ps1"]
    powershell --> rec_part["recovery-partition/"]

    rec_part --> rp_mgr["RecoveryPartitionManager.ps1"]
    rec_part --> rp_c1["Create-RecoveryPartition.ps1"]
    rec_part --> rp_rem["Remove-RecoveryPartition.ps1"]

    python --> stftp["stftp/"]
    stftp --> stftp_srv["server.py"]
    stftp --> stftp_cli["client.py"]

    testing --> dir_stats_sh["dir_stats.sh"]
    testing --> update_readme_py["update_readme.py"]
    testing --> test_readme["README.md"]

    web --> proxy["apache-reverse-proxy/"]
    proxy --> proxy_sh["apache-proxy-wizard.sh"]
    proxy --> proxy_htm["disclaimer.html"]
```

---

## 🛠️ Complete Catalog of Scripts

| Category | File / Tool | Purpose | Requirements / Dependencies |
| :--- | :--- | :--- | :--- |
| **Configuration** | [AGENTS.md](file:///C:/Users/Richard%20Troiano/.gemini/antigravity/scratch/scripts-public/.agents/AGENTS.md) | Workspace-specific rules for code change documentation and pre-commit security verification checks. | None |
| **Linux Bash** | [openssl-certtool.sh](file:///C:/Users/Richard%20Troiano/.gemini/antigravity/scratch/scripts-public/bash/openssl-certtool.sh) | Interactive utility for generating, converting, and extracting OpenSSL certificates (e.g. PEM, PFX, P12, P7B). | OpenSSL, Bash environment |
| **Linux Bash** | [script-public-merge.sh](file:///C:/Users/Richard%20Troiano/.gemini/antigravity/scratch/scripts-public/bash/script-public-merge.sh) | Restructures the workspace directories and automatically appends common file ignores to `.gitignore`. | Git repository environment |
| **PowerShell** | [openssl-certtool.ps1](file:///C:/Users/Richard%20Troiano/.gemini/antigravity/scratch/scripts-public/powershell/openssl-certtool.ps1) | Windows PowerShell equivalent of the OpenSSL certificate utility for extracting keys and certificate chains. | PowerShell, OpenSSL in system PATH |
| **PowerShell** | [check_mtu.ps1](file:///C:/Users/Richard%20Troiano/.gemini/antigravity/scratch/scripts-public/powershell/check_mtu.ps1) | Diagnoses network Maximum Transmission Unit (MTU) sizes using target host ICMP pings. | PowerShell, network interface access |
| **PowerShell** | [recovery-partition/RecoveryPartitionManager.ps1](file:///C:/Users/Richard%20Troiano/.gemini/antigravity/scratch/scripts-public/powershell/recovery-partition/RecoveryPartitionManager.ps1) | High-level interactive manager to create, remove, and manage Windows Recovery Partitions. | **Administrator privileges** |
| **Python** | [stftp/server.py](file:///C:/Users/Richard%20Troiano/.gemini/antigravity/scratch/scripts-public/python/stftp/server.py) | A simple Secure Trivial File Transfer Protocol server using TLS wrapping over standard sockets. | Python 3, OpenSSL certificate file (`cert.pem`, `key.pem`) |
| **Python** | [stftp/client.py](file:///C:/Users/Richard%20Troiano/.gemini/antigravity/scratch/scripts-public/python/stftp/client.py) | Client logic for connection and message parsing for Secure TFTP. | Python 3 |
| **Testing** | [testing/dir_stats.sh](file:///C:/Users/Richard%20Troiano/.gemini/antigravity/scratch/scripts-public/testing/dir_stats.sh) | Calculates file/folder statistics (total files, top-level folders, total subfolders, size) of a directory. | Bash environment, UNIX find utility |
| **Testing** | [testing/update_readme.py](file:///C:/Users/Richard%20Troiano/.gemini/antigravity/scratch/scripts-public/testing/update_readme.py) | Python auto-updater script to automatically refresh the README.md tools catalog based on script headers. | Python 3 |
| **Testing** | [testing/README.md](file:///C:/Users/Richard%20Troiano/.gemini/antigravity/scratch/scripts-public/testing/README.md) | Overview documentation for the testing directory. | None |
| **Report** | [directory_stats.md](file:///C:/Users/Richard%20Troiano/.gemini/antigravity/scratch/scripts-public/directory_stats.md) | Generated directory statistics report (e.g. file, folder counts, sizes). | None |
| **Web Config** | [apache-reverse-proxy/apache-proxy-wizard.sh](file:///C:/Users/Richard%20Troiano/.gemini/antigravity/scratch/scripts-public/web/apache-reverse-proxy/apache-proxy-wizard.sh) | Interactive setup wizard to automatically install and configure an Apache reverse proxy with SSL modules. | **Root privileges**, Linux with `apt` package manager |

---

## 🔒 Security & Privileges

> [!WARNING]
> Running administration scripts like `RecoveryPartitionManager.ps1` or configuration scripts like `apache-proxy-wizard.sh` will prompt for elevation (Administrator / root). Always inspect code blocks and options before executing them.

> [!TIP]
> Make sure OpenSSL is added to your environment `PATH` on Windows to leverage [openssl-certtool.ps1](file:///C:/Users/Richard%20Troiano/.gemini/antigravity/scratch/scripts-public/powershell/openssl-certtool.ps1) properly.

---

## 🚀 Recommended Action

If you want to configure or restructure this repository, you can review the files directly using the links above, or let me know which script you would like to test or optimize first.
