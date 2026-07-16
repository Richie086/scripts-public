#!/usr/bin/env bash
# Wedge 400 Switch API Build Validation Script
set -euo pipefail

echo "============================================="
echo "Running Wedge 400 Switch API Build Checks"
echo "============================================="

# 1. Check syntax of all Python files in src
echo "[1/2] Compiling Python source files..."
python3 -m py_compile $(find src/ -name "*.py")
echo "[✓] Python compile checks passed."

# 2. Check syntax of test files
echo "[2/2] Compiling Python test files..."
python3 -m py_compile $(find tests/ -name "*.py")
echo "[✓] Test compile checks passed."

echo "============================================="
echo "All compile checks completed successfully!"
echo "============================================="
