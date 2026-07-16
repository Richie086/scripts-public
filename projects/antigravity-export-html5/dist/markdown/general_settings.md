# General Settings Configuration

*Exported on: 2026-07-16 08:07:53*

This file contains the general configuration settings for the Antigravity CLI and the Gemini helper environments.

## Antigravity CLI Settings (`settings.json`)

### Configuration Parameters Summary

| Parameter | Value |
| :--- | :--- |
| **Model Selection** | `Gemini 3.5 Flash (Medium)` |
| **Agent Mode** | `plan` |
| **Color Scheme** | `dark` |
| **Editor** | `vim` |
| **Allow Non-Workspace Access** | `True` |
| **Tool Permission Mode** | `proceed-in-sandbox` |

### Permissions Configuration (`permissions.allow`)

The following commands are pre-approved to run without prompting:

- `command(/home/rtroiano/repositories/scripts-public/scripts-public/.venv/bin/python /home/rtroiano/repositories/scripts-public/scripts-public/python/manage_credentials.py set FB_PAGE_ID --value "123456")`
- `command(/home/rtroiano/repositories/scripts-public/scripts-public/.venv/bin/python /home/rtroiano/repositories/scripts-public/scripts-public/python/manage_credentials.py list)`
- `command(ssh rtroiano@192.168.1.80 'git -C ~/exitcodezero fetch origin; git -C ~/exitcodezero reset --hard origin/dev')`
- `command(ssh rtroiano@192.168.1.80 "systemctl cat nginx || true")`
- `command(ssh rtroiano@192.168.1.80 "ls -la /usr/sbin/nginx /usr/bin/nginx /sbin/nginx /usr/local/nginx/sbin/nginx 2>/dev/null || true")`
- `command(ssh -i /home/rtroiano/.ssh/id_webserver webserver@192.168.1.80 "curl -i http://localhost/")`
- `command(ssh -i /home/rtroiano/.ssh/id_webserver webserver@192.168.1.80 "curl -i 'http://localhost/admin/save_tabs?env1=Tenant+A&env2=Tenant+B&env3=Tenant+C'")`
- `command(ssh -i /home/rtroiano/.ssh/id_webserver webserver@192.168.1.80 "grep -C 2 -E '(192.168.1.80|host:)' /home/webserver/backstage-app/app-config.yaml")`

### Trusted Workspaces

- `/home/rtroiano`
- `/home/rtroiano/scripts-public`
- `/home/rtroiano/scripts-public/scripts-public/projects/apache-reverse-proxy-config-generator`
- `/home/rtroiano/scripts-public/scripts-public/web/apache-reverse-proxy`
- `/home/rtroiano/repositories/scripts-public`
- `/home/rtroiano/repositories/scripts-public/scripts-public`
- `/home/rtroiano/repositories/scripts-public/scripts-public/projects/apache-reverse-proxy-config-generator`
- `/home/rtroiano/repositories/scripts-public/scripts-public/web/apache-reverse-proxy`
- `/home/rtroiano/repositories/scripts/bash`
- `/home/rtroiano/Downloads`
- `/home/rtroiano/repositories/exitcodezero`

### Raw JSON Settings

```json
{
  "agentMode": "plan",
  "allowNonWorkspaceAccess": true,
  "artifactReviewPolicy": "agent-decides",
  "colorScheme": "dark",
  "editor": "vim",
  "enableTelemetry": false,
  "model": "Gemini 3.5 Flash (Medium)",
  "permissions": {
    "allow": [
      "command(/home/rtroiano/repositories/scripts-public/scripts-public/.venv/bin/python /home/rtroiano/repositories/scripts-public/scripts-public/python/manage_credentials.py set FB_PAGE_ID --value \"123456\")",
      "command(/home/rtroiano/repositories/scripts-public/scripts-public/.venv/bin/python /home/rtroiano/repositories/scripts-public/scripts-public/python/manage_credentials.py list)",
      "command(ssh rtroiano@192.168.1.80 'git -C ~/exitcodezero fetch origin; git -C ~/exitcodezero reset --hard origin/dev')",
      "command(ssh rtroiano@192.168.1.80 \"systemctl cat nginx || true\")",
      "command(ssh rtroiano@192.168.1.80 \"ls -la /usr/sbin/nginx /usr/bin/nginx /sbin/nginx /usr/local/nginx/sbin/nginx 2>/dev/null || true\")",
      "command(ssh -i /home/rtroiano/.ssh/id_webserver webserver@192.168.1.80 \"curl -i http://localhost/\")",
      "command(ssh -i /home/rtroiano/.ssh/id_webserver webserver@192.168.1.80 \"curl -i 'http://localhost/admin/save_tabs?env1=Tenant+A&env2=Tenant+B&env3=Tenant+C'\")",
      "command(ssh -i /home/rtroiano/.ssh/id_webserver webserver@192.168.1.80 \"grep -C 2 -E '(192.168.1.80|host:)' /home/webserver/backstage-app/app-config.yaml\")"
    ]
  },
  "runningLightSpeed": "fast",
  "statusLine": {
    "type": "command",
    "command": "",
    "enabled": false
  },
  "toolPermission": "proceed-in-sandbox",
  "trustedWorkspaces": [
    "/home/rtroiano",
    "/home/rtroiano/scripts-public",
    "/home/rtroiano/scripts-public/scripts-public/projects/apache-reverse-proxy-config-generator",
    "/home/rtroiano/scripts-public/scripts-public/web/apache-reverse-proxy",
    "/home/rtroiano/repositories/scripts-public",
    "/home/rtroiano/repositories/scripts-public/scripts-public",
    "/home/rtroiano/repositories/scripts-public/scripts-public/projects/apache-reverse-proxy-config-generator",
    "/home/rtroiano/repositories/scripts-public/scripts-public/web/apache-reverse-proxy",
    "/home/rtroiano/repositories/scripts/bash",
    "/home/rtroiano/Downloads",
    "/home/rtroiano/repositories/exitcodezero"
  ],
  "verbosity": "low"
}
```

## Gemini Config (`config.json`)

```json
{
  "userSettings": {
    "remoteControlHostname": "garage-desktop-frozen-zone"
  }
}
```
