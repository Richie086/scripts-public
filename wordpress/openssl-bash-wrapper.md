# The Ultimate OpenSSL Bash Wrapper: Painless Certificate Management

If you've ever found yourself staring at a blinking cursor, desperately trying to remember the arcane OpenSSL syntax required to rip a private key from a `.pfx` file, take comfort—you're in good company. Certificate management is a high-stakes chore, yet OpenSSL’s command-line arguments are infamously hard to recall.

Enter this bash script: an interactive, secure, and intuitive wrapper for OpenSSL. It eliminates the trial-and-error from certificate conversions, extractions, and validations.

Here is a deep dive into what this utility accomplishes, why its security features matter, and how it can streamline your daily operations.

## What Does This Script Do?

At its heart, the script ingests a combined certificate file (like `.pfx`, `.p12`, or `.p7b`) and launches an interactive menu allowing you to extract precisely the components you require.

### Key Features

*   **Format Support:** Natively processes `.pfx`, `.p12`, and `.p7b` archives. *(Note: `.p7b` files strictly contain public certificates, so the script smartly disables private key extraction for these formats).*
*   **Granular Extraction:** Effortlessly pull public certificates (`.cer`), private keys (`.key`), CA chains (Root/Intermediate), or fully combined `.pem` files.
*   **Built-In Security:**
    *   **Memory Wiping:** Utilizes the `trap` command to ensure the certificate password (`CERT_PASS`) is instantly purged from system memory upon exit or interruption (Ctrl+C).
    *   **Secure Permissions:** Extracted private keys and `.pem` bundles are automatically secured with `chmod 600` permissions, ensuring only the file owner can read them.
*   **Certificate Verification:** Features an advanced utility to compute and compare the MD5 modulus of your `.cer` and `.key` files, guaranteeing a perfect mathematical match prior to deployment.
*   **Cloud & Kubernetes Ready:** Includes a Base64 encoder that outputs your certificate as a continuous string—ideal for seamless integration into Kubernetes Secrets or cloud config files.
*   **CSR Generation:** Empowers you to forge a fresh Certificate Signing Request (CSR) directly from an extracted private key.

## How to Get the Script

Rather than making you copy and paste a massive block of code, the script is available directly from my public GitHub repository, where I maintain all my utility tools.

You have two straightforward options:

### Option 1: Download the Raw Script

If you're only interested in this specific utility, you can download the raw file via the link below, or directly in your terminal using `curl`/`wget`:

[Download openssl-certtool.sh (Raw GitHub Link)](https://raw.githubusercontent.com/Richie086/scripts-public/refs/heads/main/projects/openssl-output-generator/openssl-certtool.sh)

```bash
curl -O https://raw.githubusercontent.com/Richie086/scripts-public/refs/heads/main/projects/openssl-output-generator/openssl-certtool.sh
```

### Option 2: Clone the Full Repository

If you'd like to explore this script alongside my other public tools, you can clone the entire repository:

```bash
git clone https://github.com/Richie086/scripts-public.git
```

Navigate to `projects/openssl-output-generator/` within the cloned directory to locate the tool.

## How to Use It

### 1. Make it Executable

Regardless of your download method, you must grant the script execution permissions before running it:

```bash
chmod +x openssl-certtool.sh
```

### 2. Launch the Tool

It is highly recommended to kick things off by running the script with the `--help` flag to get acquainted with the available options:

```bash
./openssl-certtool.sh --help
```

**Command-Line Arguments:** For the fastest workflow, provide your input certificate and the desired output path directly at execution. This skips the initial prompts and drops you straight into the action menu:

```bash
./openssl-certtool.sh --input /path/to/mycert.pfx --output /tmp/extracted_cert
```

**Interactive Fallback:** If you execute the script without arguments, it gracefully falls back to an interactive prompt, asking for the file path before loading the menu:

```bash
./openssl-certtool.sh
```

### 3. Navigate the Menu

Once your file and password are validated, you'll be greeted by a comprehensive 12-option menu:

*   **Options 1-7 (Extraction):** Select which components you need. Option 7 is exceptionally handy for web servers (like Nginx or HAProxy), compiling a fully chained `.pem` file containing the private key, primary certificate, and CA chain in the proper sequence.
*   **Option 8 (View Info):** Instantly review the expiration dates and Subject Alternative Names (SANs) attached to your certificate.
*   **Option 9 (Verify Match):** Execute this post-extraction to confirm your `.cer` and `.key` mathematically align.
*   **Option 10 & 11 (Advanced):** Generate Base64 strings for deployments or mint a brand-new CSR.
*   **Option 12 (Exit):** Safely terminates the tool, triggering the secure password memory wipe.

## Latest Updates to openssl-certtool.sh

*   **Automatic Format Probing:** The script now dynamically inspects PKCS#7 and PKCS#12 file structures, moving away from relying solely on file extensions.
*   **Strict Argument Validation:** Enforces the presence of both `--input` and `--output` arguments at startup to prevent interactive path loops.
*   **Certificate Expiration Checker:** Added an option to compute and display the remaining days of certificate validity.
