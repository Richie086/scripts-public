<!-- AUTO-GENERATED MERMAID START -->
<!-- This Mermaid diagram and inventory are auto-generated. Do not edit directly. -->

## Directory structure

<details>
<summary>Show directory tree diagram for `powershell`</summary>

```mermaid
treeView-beta
powershell/
  Calculate-FolderStats.ps1
  check_mtu.ps1
  openssl-certtool.ps1
  Publish-WordPressPost.ps1
  README.md
  recovery-partition/
    Create-RecoveryPartition.ps1
    Create-RecoveryPartition2.ps1
    Create-RecoveryPartition3.ps1
    README.md
    RecoveryPartitionManager.ps1
    Remove-RecoveryPartition.ps1
```

</details>

## Files and folders

- Calculate-FolderStats.ps1 — text/config file (2425 bytes)
- check_mtu.ps1 — text/config file (5541 bytes)
- openssl-certtool.ps1 — text/config file (10959 bytes)
- Publish-WordPressPost.ps1 — text/config file (1560 bytes)
- README.md — text/config file (2625 bytes)
- recovery-partition/ — Directory with 6 items
  - Create-RecoveryPartition.ps1 — text/config file (2821 bytes)
  - Create-RecoveryPartition2.ps1 — text/config file (1141 bytes)
  - Create-RecoveryPartition3.ps1 — text/config file (2015 bytes)
  - README.md — text/config file (970 bytes)
  - RecoveryPartitionManager.ps1 — text/config file (9398 bytes)
  - Remove-RecoveryPartition.ps1 — text/config file (1351 bytes)

<!-- AUTO-GENERATED MERMAID END -->

# PowerShell

## openssl-certtool.ps1

A Windows PowerShell version of the OpenSSL certificate utility.

### Supported input formats
- `.pfx`
- `.p12`
- `.p7b`

### Features
- Detects whether a `.pfx`/`.p12` file requires a password and prompts only when needed
- Automatically detects `.p7b` format as DER or PEM
- Extracts:
  - public certificate (`.cer`)
  - CA chain (`_ca_chain.cer`)
  - PEM bundles and private keys for `.pfx`/`.p12`
  - CSR generation from the extracted private key
- Provides interactive menu-driven operations

### Requirements
- Windows PowerShell
- OpenSSL installed and available on `PATH`

### Usage
```powershell
.\openssl-certtool.ps1 -Input .\cert.pfx
.\openssl-certtool.ps1 -Input .\cert.p7b -Output .\wildcard_extremasarcasm_org
```

### Help
```powershell
.\openssl-certtool.ps1 -Help
```

### Notes
- `.p7b` files are certificate bundles only and do not contain private keys.
- The script will warn when a requested operation is not supported for `.p7b` input.

### Bash version
A Bash version of this utility is available at `projects/openssl-output-generator/openssl-certtool.sh`. Its interactive menu includes an option `7` to create a combined `.pem` file containing the private key, primary certificate, then the CA chain.
