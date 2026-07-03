<!-- AUTO-GENERATED MERMAID START -->
<!-- This Mermaid diagram is auto-generated. Do not edit directly. -->

## Directory structure

<details>
<summary>Show GitGraph diagram for `powershell`</summary>

```mermaid
gitGraph
    commit id: "root: powershell"
    commit id: "file: Calculate-FolderStats.ps1 (2425 bytes)"
    commit id: "file: check_mtu.ps1 (5541 bytes)"
    commit id: "file: openssl-certtool.ps1 (10959 bytes)"
    commit id: "file: Publish-WordPressPost.ps1 (1560 bytes)"
    commit id: "file: README.md (1789 bytes)"
    commit id: "dir: recovery-partition (6 entries)"
```

</details>

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
