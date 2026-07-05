<!-- AUTO-GENERATED MERMAID START -->
<!-- This Mermaid diagram is auto-generated. Do not edit directly. -->

## Directory structure

<details>
<summary>Show directory tree diagram for `openssl-certtool`</summary>

```mermaid
graph TD
	root["openssl-certtool"]:::root --> n1["openssl-certtool.sh"]:::file-sh
	root["openssl-certtool"]:::root --> n2["README.md"]:::file-md
classDef root fill:#2563eb,stroke:#1e40af,stroke-width:2px,color:#ffffff;
classDef folder fill:#fbbf24,stroke:#d97706,stroke-width:1px,color:#451a03;
classDef file-md fill:#dbeafe,stroke:#3b82f6,stroke-width:1px,color:#1e3a8a;
classDef file-sh fill:#ccfbf1,stroke:#0d9488,stroke-width:1px,color:#134e4a;
```

</details>

<!-- AUTO-GENERATED MERMAID END -->

# openssl-certtool.sh

## Intended function
Interactive OpenSSL utility for extracting and validating certificate artifacts from `.pfx`, `.p12`, or `.p7b` inputs.

It can:
- Extract `.cer`, `.key`, `.pem`, and CA chain files
- Build a combined PEM in the order key -> cert -> chain
- Verify cert/key pair matching
- Print SAN/expiration details and generate CSR

## How to use
Required args:
- `--input <path>`: source cert bundle (`.pfx`, `.p12`, or `.p7b`)
- `--output <prefix>`: output base path/name

```bash
bash openssl-certtool.sh --input ./mycert.pfx --output /tmp/mycert
```

Then select menu options `1-13` for extraction and validation tasks.

## Example
```bash
cd /path/to/scripts-public/bash/openssl-certtool
bash openssl-certtool.sh --input ./corp-cert.p12 --output ./corp-cert
```

## Warnings
- Generated private keys/PEM material are sensitive secrets.
- Some operations write unencrypted private keys to disk.
- Protect output files and directories; do not commit cert/key files to Git.
- The script uses OpenSSL legacy flags for compatibility; verify artifacts before production use.
