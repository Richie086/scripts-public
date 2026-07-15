#!/bin/bash
# TERMINUS Compiler Helper Script
# Strict shell options for safety and reliability
set -euo pipefail

echo "Compiling terminus.sh to binary executable terminus..."
# Compile script using shc (Shell Script Compiler) with relaxed security for compatibility
shc -r -f terminus.sh -o terminus

echo "Making sure binary is executable..."
chmod +x terminus

echo "Verification: checking built binary details..."
file ./terminus
echo "Checking binary version/help output:"
./terminus --help || true
