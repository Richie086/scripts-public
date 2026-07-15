#!/usr/bin/env bash
# TERMINUS Build/Validation Helper Script
# Strict shell options for safety and reliability
set -euo pipefail

echo "Validating terminus.py syntax..."
python3 -m py_compile terminus.py

echo "Making sure script is executable..."
chmod +x terminus.py

echo "Verification: checking built script syntax..."
python3 -c "import py_compile; py_compile.compile('terminus.py')"
echo "Valid! Terminus Python script is ready."
