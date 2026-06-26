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
