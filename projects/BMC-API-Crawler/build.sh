#!/usr/bin/env bash
# BMC API Crawler compile check script
set -euo pipefail

echo "============================================="
echo "Running BMC API Crawler Build Checks"
echo "============================================="

# 1. Compile check all source files
echo "[1/2] Compiling Python source files..."
python3 -m compileall src/
echo "[✓] Python compile checks passed."

# 2. Compile check test suite
echo "[2/2] Compiling Python test files..."
python3 -m compileall tests/
echo "[✓] Test compile checks passed."

echo "============================================="
echo "All compile checks completed successfully!"
echo "============================================="
