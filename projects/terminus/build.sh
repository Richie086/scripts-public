#!/bin/bash
# NETMON V3 Compiler Helper Script
# Strict shell options for safety and reliability
set -euo pipefail

echo "Compiling netmon.sh to binary executable netmon..."
# Compile script using shc (Shell Script Compiler) with relaxed security for compatibility
shc -r -f netmon.sh -o netmon

echo "Making sure binary is executable..."
chmod +x netmon

echo "Verification: checking built binary details..."
file ./netmon
echo "Checking binary version/help output:"
./netmon --help || true
