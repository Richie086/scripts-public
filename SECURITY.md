# Security Policy

## Reporting a Security Concern

If you find any security vulnerabilities, credentials, or general issues with these scripts that you think might be a concern:
1. Go to the **Issues** tab of this repository on GitHub.
2. Click on **New Issue**.
3. Provide a clear description of the concern, including the script name and the relevant code lines.
4. I will investigate and address the issue as soon as possible.

## ⚠️ Disclaimer: Running Third-Party Scripts

Running executable scripts downloaded directly from the internet—including this or any other person's GitHub repository—without checking the contents is generally a bad idea and poses significant security risks.

Before running any script on your machine, it is highly recommended to:
- **Inspect the code**: Open the script in a text editor and read through it to understand exactly what commands it executes.
- **Verify commands**: Look for commands that modify system files, install packages, require `sudo` privileges, or perform network requests.
- **Test safely**: Run and test scripts inside a safe, isolated environment (such as a virtual machine, sandbox, or test container) before running them on your main production system.
