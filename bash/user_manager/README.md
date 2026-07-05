<!-- AUTO-GENERATED MERMAID START -->
<!-- This Mermaid diagram is auto-generated. Do not edit directly. -->

## Directory structure

<details>
<summary>Show directory tree diagram for `user_manager`</summary>

```mermaid
graph TD
	root["user_manager"]:::root --> n1["README.md"]:::file-md
	root["user_manager"]:::root --> n2["user_manager.sh"]:::file-sh
classDef root fill:#2563eb,stroke:#1e40af,stroke-width:2px,color:#ffffff;
classDef folder fill:#fbbf24,stroke:#d97706,stroke-width:1px,color:#451a03;
classDef file-md fill:#dbeafe,stroke:#3b82f6,stroke-width:1px,color:#1e3a8a;
classDef file-sh fill:#ccfbf1,stroke:#0d9488,stroke-width:1px,color:#134e4a;
```

</details>

<!-- AUTO-GENERATED MERMAID END -->

# user_manager.sh

## Intended function
Advanced Linux user-management tool for Ubuntu with interactive and CLI modes.

It can:
- Create users with optional UID/GID/home/shell
- Add users to groups
- Configure sudo access profiles
- Record operations in an audit log
- Run in dry-run mode for safe previews

## How to use
Interactive mode:

```bash
sudo bash user_manager.sh
```

CLI mode example:

```bash
sudo bash user_manager.sh -username devops1 -password 'StrongPass123!' -UID 1101 -GID 1101 -home /home/devops1 -terminal /bin/bash
```

Dry run:

```bash
sudo bash user_manager.sh -username testuser --dry-run
```

## Warnings
- Requires root privileges and modifies local user/group/sudo state.
- Passwords provided as CLI arguments may be exposed via shell history/process list.
- Invalid sudo rules can affect privilege management; validate carefully.
- Prefer dry-run and controlled testing before production usage.
