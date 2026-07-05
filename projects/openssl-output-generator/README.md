<!-- AUTO-GENERATED MERMAID START -->
<!-- This Mermaid diagram is auto-generated. Do not edit directly. -->

## Directory structure

<details>
<summary>Show directory tree diagram for `openssl-output-generator`</summary>

```mermaid
graph TD
	root["openssl-output-generator"]:::root --> n1["README.md"]:::file-md
classDef root fill:#2563eb,stroke:#1e40af,stroke-width:2px,color:#ffffff;
classDef folder fill:#fbbf24,stroke:#d97706,stroke-width:1px,color:#451a03;
classDef file-md fill:#dbeafe,stroke:#3b82f6,stroke-width:1px,color:#1e3a8a;
```

</details>

<!-- AUTO-GENERATED MERMAID END -->

# OpenSSL Output Generator (Bash)

This folder contains a Bash interactive utility `openssl-certtool.sh` to extract certificates and keys from `.pfx`, `.p12`, and `.p7b` files using OpenSSL.

Key features:
- Extract public certificate (`.cer`)
- Extract private key (`.key`) for `.pfx`/`.p12`
- Extract `.pem` bundles
- Extract CA chain (`_ca_chain.cer`)
- Create a combined `.pem` file with the following order: private key, primary certificate, then root/chain. This is available as option 7 in the interactive menu.

Usage:

```bash
bash projects/openssl-output-generator/openssl-certtool.sh --input /path/to/cert.pfx --output /tmp/mycert
```

Then follow the interactive menu. Select `7` to create the combined PEM (private key first, cert second, CA chain last).

Notes:
- `.p7b` inputs do not contain private keys; combined PEM is not supported for `.p7b`.
- Output files are secured with `chmod 600` where applicable.
