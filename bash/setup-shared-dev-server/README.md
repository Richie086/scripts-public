# Shared Development Server Environment Setup (`setup_shared_dev_server.sh`)

Automates the configuration of a multi-user Linux development server directory. It configures shared groups, directory ownership, SetGID bits, and POSIX Access Control Lists (ACLs) so that multiple developers can collaborate within a shared project directory without file permission issues.

## Features

- **Shared Group Creation**: Creates a target developers group (`devs` by default).
- **Directory Setup**: Creates a shared working directory (`/srv/projects` by default).
- **SetGID Permission Enforcement**: Sets the SetGID bit (`g+s`) on the directory so all new files automatically inherit the shared group ownership.
- **POSIX ACL Inheritance**: Uses `setfacl` to ensure new files and subdirectories automatically inherit read/write/execute permissions for all members of the group.

## Usage

```bash
# Run with defaults (Group: devs, Directory: /srv/projects)
./setup_shared_dev_server.sh

# Run with custom group and directory via environment variables
DEV_GROUP="engineering" SHARED_DIR="/opt/projects" ./setup_shared_dev_server.sh
```

## Adding Developers

Once configured, add developers to the group:
```bash
sudo usermod -aG devs <username>
```
*Note: Users must log out and back in for group membership changes to take effect.*
