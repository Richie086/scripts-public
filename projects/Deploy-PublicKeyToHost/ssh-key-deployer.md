# SSH Key Generator & Remote Deployment Tool (`ssh-key-deployer.sh`)

A production-grade, interactive Bash script designed to securely generate an Ed25519 keypair, deploy the public key to a remote host, configure permissions, and verify the connection.

The script features a modern dark-themed visual design with 256-color ANSI rendering and prints every command it runs in real time so you know exactly what is happening.

---

## Features

- **Robust SSH Standards**: Generates highly secure `Ed25519` keypairs by default (faster, smaller, and more secure than legacy RSA keys).
- **Interactive Prompts**: Gathers connection details (remote hostname, username, and custom port) and custom key names.
- **Safety & Permissions**:
  - Automatically verifies and secures the local `~/.ssh` directory structure (`700` permissions).
  - Handles remote permissions on target servers (`700` for `~/.ssh` and `600` for `authorized_keys`).
- **Structured Installation**: Uses `ssh-copy-id` if available; automatically falls back to manual SSH piping (`cat | ssh ...`) if the utility is missing.
- **Command Transparency**: Prints every command string before executing it (`[ COMMAND ] ↳ ...`).
- **Comprehensive Dual Verification**:
  - **Private Key Authentication**: Verifies that standard key-based logins succeed.
  - **Public Key Path Resolution**: Verifies if the local SSH client can resolve the matching private key when referencing the public key path with `-i` (a common user requirement).
- **Visual Dark Theme**: Styled with Indigo/Purple, Cyan, and Neon Green highlighting for optimal contrast in dark-themed terminals.

---

## Execution Walkthrough

The script runs in the following sequence:

1. **Step 0: Verifying Local SSH Environment**: Creates `~/.ssh` locally if missing and locks it down to `chmod 700`.
2. **Step 1: Gathering Remote Server Details**: Prompts for remote hostname, username, and port (with sensible defaults).
3. **Step 2: Configuring SSH Key Generation**: Configures key naming (defaults to a hostname-based structure like `id_ed25519_hostname`) and handles optional passphrases.
4. **Step 3: Deploying Public Key to Remote Host**: Uploads the public key using `ssh-copy-id` or standard piping fallback.
5. **Step 4: Verifying Remote Connections**: Performs connection tests using `ssh -o BatchMode=yes` (preventing password fallback prompts during verification) using both private and public keys.
6. **Step 5: Setup Summary Report**: Displays a detailed setup summary and the exact login command.

---

## Usage Examples

### 1. Execute the Script
Run the script from the directory containing it:
```bash
./ssh-key-deployer.sh
```

### 2. Manual Login command (Once configured)
To log in securely without a password using your new key:
```bash
ssh -i ~/.ssh/id_ed25519_your_host -p 22 username@your_host
```

---

## Special Configuration: Synology NAS (DSM 7+) Setup

Synology NAS systems running DSM 7 have strict security constraints. Below are the steps required to ensure this script's key-based authentication works correctly on Synology:

### 1. Enable User Home & SSH Services in DSM
* **User Home Service**: Go to **Control Panel > User & Group > Advanced > User Home** and tick **Enable user home service**. Without this, home directories do not exist, and SSH cannot locate `~/.ssh/authorized_keys`.
* **SSH Service**: Go to **Control Panel > Terminal & SNMP > Terminal** and tick **Enable SSH service**.

### 2. Verify Administrators Group Membership
By default on DSM 7, SSH access is restricted to accounts in the **administrators** group.
* Go to **Control Panel > User & Group**.
* Edit your target user and ensure they belong to the **administrators** group under the **Groups** tab.

### 3. Restrict Directory Permissions (Crucial)
Synology home directories often inherit relaxed permissions which causes the SSH daemon to reject key logins. Execute the following on the NAS (via password login) to fix them:
```bash
# 1. Protect home folder
chmod 755 ~

# 2. Protect SSH config folder
chmod 700 ~/.ssh

# 3. Protect authorized keys file
chmod 600 ~/.ssh/authorized_keys
```

### 4. Optional sshd_config Verification
If keys are still rejected, verify that key authentication is active in `/etc/ssh/sshd_config` by logging into the NAS, elevating to root (`sudo -i`), and verifying the following values:
```text
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
```
*If you modify this file, restart the SSH service:*
```bash
synosystemctl restart sshd
```
