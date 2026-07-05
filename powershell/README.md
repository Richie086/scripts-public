<!-- AUTO-GENERATED MERMAID START -->
<!-- This Mermaid diagram is auto-generated. Do not edit directly. -->

## Directory structure

<details>
<summary>Show directory tree diagram for `powershell`</summary>

```mermaid
graph TD
	root["powershell"]:::root --> n1("recovery-partition"):::folder
	root["powershell"]:::root --> n2["README.md"]:::file-md
	root["powershell"]:::root --> n3["Publish-WordPressPost.ps1"]:::file-ps1
	root["powershell"]:::root --> n4["check_mtu.ps1"]:::file-ps1
	root["powershell"]:::root --> n5["openssl-certtool.ps1"]:::file-ps1
	root["powershell"]:::root --> n6["Calculate-FolderStats.ps1"]:::file-ps1
	n1 --> n1_6["README.md<br>Create-RecoveryPartition2.ps1<br>Remove-RecoveryPartition.ps1<br>Create-RecoveryPartition.ps1<br>Create-RecoveryPartition3.ps1<br>RecoveryPartitionManager.ps1"]:::file-bundle
classDef root fill:#2563eb,stroke:#1e40af,stroke-width:2px,color:#ffffff;
classDef folder fill:#fbbf24,stroke:#d97706,stroke-width:1px,color:#451a03;
classDef file-bundle fill:#e2e8f0,stroke:#64748b,stroke-width:1px,color:#334155;
classDef file-md fill:#dbeafe,stroke:#3b82f6,stroke-width:1px,color:#1e3a8a;
classDef file-ps1 fill:#e0e7ff,stroke:#6366f1,stroke-width:1px,color:#312e81;
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
