<!-- AUTO-GENERATED MERMAID START -->
<!-- This Mermaid diagram and inventory are auto-generated. Do not edit directly. -->

## Directory structure

<details>
<summary>Show directory tree diagram for `user_manager`</summary>

```mermaid
treeView-beta
user_manager/
  README.md
  user_manager.sh
```

</details>

## Files and folders

- README.md — text/config file (1396 bytes)
- user_manager.sh — text/config file (8585 bytes)

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
