# Model Context Protocol (MCP) Configuration

*Exported on: 2026-07-16 08:10:06*

This file summarizes the configured MCP servers used by the Antigravity agent to connect to external tools and services.

## Source: User Config (`~/.gemini/config/mcp_config.json`)

| Server Name | Command | Arguments |
| :--- | :--- | :--- |
| **github** | `docker` | `run`, `-i`, `--rm`, `-v`, `/var/run/docker.sock:/var/run/docker.sock`, `ghcr.io/modelcontextprotocol/servers/github` |

### Raw JSON Configuration

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
        "GITHUB_PERSONAL_ACCESS_TOKEN": "[REDACTED]"
      }
    }
  }
}
```

## Source: Antigravity Config (`~/.gemini/antigravity/mcp_config.json`)

| Server Name | Command | Arguments |
| :--- | :--- | :--- |
| **github-mcp-server** | `docker` | `run`, `-i`, `--rm`, `-e`, `GITHUB_PERSONAL_ACCESS_TOKEN`, `ghcr.io/github/github-mcp-server`, `stdio`, `--log-file=/tmp/github-mcp-server.log` |
| **GitKraken** | `/home/rtroiano/.local/share/GitKrakenCLI/versions/gk_3_1_70-alpha_2/gk_3_1_70-alpha_2` | `mcp`, `--host=antigravity`, `--session=kepler` |

### Raw JSON Configuration

```json
{
  "mcpServers": {
    "github-mcp-server": {
      "$typeName": "exa.cascade_plugins_pb.CascadePluginCommandTemplate",
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server",
        "stdio",
        "--log-file=/tmp/github-mcp-server.log"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "[REDACTED]"
      }
    },
    "GitKraken": {
      "args": [
        "mcp",
        "--host=antigravity",
        "--session=kepler"
      ],
      "command": "/home/rtroiano/.local/share/GitKrakenCLI/versions/gk_3_1_70-alpha_2/gk_3_1_70-alpha_2",
      "type": "stdio"
    }
  }
}
```

