<!-- AUTO-GENERATED MERMAID START -->
<!-- This Mermaid diagram is auto-generated. Do not edit directly. -->

```mermaid
graph TD
n0["powershell"]
n1["Calculate-FolderStats.ps1"]
n2["check_mtu.ps1"]
n3["openssl-certtool.ps1"]
n4["Publish-WordPressPost.ps1"]
n5["README.md"]
n6["recovery-partition/"]
n7["Create-RecoveryPartition.ps1"]
n8["Create-RecoveryPartition2.ps1"]
n9["Create-RecoveryPartition3.ps1"]
n10["RecoveryPartitionManager.ps1"]
n11["Remove-RecoveryPartition.ps1"]
n0 --> n1
n0 --> n2
n0 --> n3
n0 --> n4
n0 --> n5
n0 --> n6
n6 --> n7
n6 --> n8
n6 --> n9
n6 --> n10
n6 --> n11
```

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
