# Workspace Rules

## WordPress REST API Authentication
* When writing scripts or configuring integrations to interact with the WordPress REST API, always prompt for or use **WordPress Application Passwords** (24 characters separated by spaces: `xxxx xxxx xxxx xxxx xxxx xxxx`) instead of standard user login passwords, as the API restricts basic authentication for standard passwords by default.

## Command Execution Guardrails
* Do not execute interactive commands (e.g., text editors like `vi`, `nano`, `emacs`) or commands requiring `sudo` password entry within the non-interactive background terminal. 
* Instead, immediately notify the user of the command's interactive nature and provide the exact command line for them to run in their own local terminal.
