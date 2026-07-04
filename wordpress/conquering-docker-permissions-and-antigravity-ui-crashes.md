# How I Conquered Docker Permissions and Antigravity UI Crashes for MCP Servers

Have you ever tried setting up a Model Context Protocol (MCP) server via Docker, only to get slammed by a permission error—and then, right when you think you've fixed it, your entire IDE crashes?

If you've been trying to connect a containerized MCP server (like the GitHub MCP server) to Google Antigravity, you might have found yourself trapped exactly where I was: stuck between a `/var/run/docker.sock` permission denial and a cryptic `TypeError: Cannot read properties of null (reading '__store')` UI crash.

After hours of tearing my hair out, I finally figured out what was going on. Here is my straightforward, step-by-step guide to fixing the permissions cleanly and bypassing the broken UI so you can get back to coding.

---

## Phase 1: Resolving Docker Socket Permissions

When my MCP server first attempted to boot, it needed to talk to the Docker daemon. Naturally, I was hit with a permission denied error for `/var/run/docker.sock` because my user account lacked the necessary rights.

The standard fix is simple enough. I added my user to the `docker` group:

```bash
sudo usermod -aG docker $USER
```

### The "Command Not Found" Trap

Normally, you would run `newgrp docker` or `sg docker -c "bash"` to refresh your terminal's group assignments without logging out. However, because I was working in a minimalist environment, my terminal rejected both commands with "command not found."

If you are running into this same wall, here are the guaranteed workarounds I used:

* **The Virtual/Cloud Session Reset**: Completely close your IDE terminal or SSH connection and open a fresh one.
* **The Login Shell Simulation**: Force a reload of your user's group configurations by running:
  ```bash
  su - $USER
  ```
  (and entering your password).
* **The Direct Bypass**: If modifying groups simply will not propagate in your custom setup, grant your user explicit ownership of the socket file:
  ```bash
  sudo chown $USER /var/run/docker.sock
  ```

> [!IMPORTANT]
> Running `sudo chown $USER /var/run/docker.sock` is a heavy-handed bypass, but it instantly grants your active user read and write access, allowing the server to initialize without a reboot. Never use `chmod 777` as an alternative, as it creates a severe security vulnerability!

---

## Phase 2: Bypassing the Antigravity "__store" Bug

Once I solved the Docker permissions, I expected smooth sailing. Instead, I opened the Antigravity Settings panel and was greeted by this nightmare: 

```
TypeError: Cannot read properties of null (reading '__store')
```

If you are seeing this, don't panic. This is not your fault, and it is not a Docker issue. This is a known UI packaging bug in the Antigravity workspace configuration panel. When the MCP server successfully returned its local configuration data, it inadvertently triggered a rendering crash in the editor's state manager.

Because the visual settings panel was completely glitching out, I had to bypass the graphical interface and edit the underlying configuration file directly. Here is exactly how I did it.

### Step 1: Open the Raw Configuration File

Antigravity stores its central MCP server configuration in your home directory. Open your terminal and edit this file:

```bash
nano ~/.gemini/config/mcp_config.json
```

### Step 2: Inject the Server JSON

Inside this file, you need to structure your `mcpServers` block. If your file is empty, just paste the block below. Be sure to swap out the placeholder with your actual GitHub Personal Access Token.

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/var/run/docker.sock:/var/run/docker.sock",
        "ghcr.io/modelcontextprotocol/servers/github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_FINE_GRAINED_GITHUB_TOKEN"
      }
    }
  }
}
```

### Step 3: Clear the Frozen UI Cache

To completely unstick the Antigravity client from that null render crash, I had to purge the corrupted local app layout state before booting it back up. Run this in your terminal:

```bash
rm -rf ~/.config/Antigravity/Local\ Storage
```

### Step 4: Restart and Verify

Now that the cache was cleared and my configuration was hardcoded into the JSON file, I restarted Google Antigravity entirely. 

To test if the bridge was fully active without touching the broken settings UI, I opened the Agentic Panel (`Ctrl + Alt + B`) and issued a direct prompt:

> "Please check your connection to the GitHub MCP server and list my available repositories."

The AI successfully bypassed the broken UI, executed my direct JSON container settings, read the mounted Docker socket, and hooked straight into my GitHub account.
