#!/usr/bin/env bash
# Flag / help tests for ai-devbox-init.sh (no live install, no gum required).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/ai-devbox-init.sh"
pass=0
fail=0

assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    echo "  PASS  $label"
    pass=$((pass + 1))
  else
    echo "  FAIL  $label (expected=$expected actual=$actual)"
    fail=$((fail + 1))
  fi
}

assert_contains() {
  local label="$1" needle="$2" haystack="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    echo "  PASS  $label"
    pass=$((pass + 1))
  else
    echo "  FAIL  $label (missing: $needle)"
    fail=$((fail + 1))
  fi
}

echo "==> ai-devbox-init flag tests"
echo "    script: $SCRIPT"

set +e
out="$(bash "$SCRIPT" 2>&1)"
ec=$?
set -e
assert_eq "no-args exit 0" "0" "$ec"
assert_contains "no-args shows Usage" "Usage: ./ai-devbox-init.sh" "$out"

set +e
out="$(bash "$SCRIPT" --help 2>&1)"
ec=$?
set -e
assert_eq "--help exit 0" "0" "$ec"
assert_contains "--help names script" "ai-devbox-init.sh" "$out"
assert_contains "--help lists --dry-run" "--dry-run" "$out"
assert_contains "--help lists --run" "--run" "$out"

set +e
out="$(bash "$SCRIPT" -h 2>&1)"
ec=$?
set -e
assert_eq "-h exit 0" "0" "$ec"

set +e
out="$(bash "$SCRIPT" help 2>&1)"
ec=$?
set -e
assert_eq "help exit 0" "0" "$ec"

set +e
out="$(bash "$SCRIPT" --bogus 2>&1)"
ec=$?
set -e
assert_eq "unknown flag exit 1" "1" "$ec"
assert_contains "unknown flag message" "Unknown argument: --bogus" "$out"

set +e
out="$(bash "$SCRIPT" --run --dry-run 2>&1)"
ec=$?
set -e
assert_eq "--run + --dry-run exit 1" "1" "$ec"
assert_contains "mutual exclusion message" "Cannot use --run and --dry-run together" "$out"

set +e
out="$(bash "$SCRIPT" -r -n 2>&1)"
ec=$?
set -e
assert_eq "-r + -n exit 1" "1" "$ec"

# Only --help-related flags should not enter interactive install.
# Confirm help does not mention the old wrong script name.
set +e
out="$(bash "$SCRIPT" --help 2>&1)"
set -e
if [[ "$out" == *"install-linux-dev-env.sh"* ]]; then
  echo "  FAIL  help must not mention install-linux-dev-env.sh"
  fail=$((fail + 1))
else
  echo "  PASS  help has no stale script name"
  pass=$((pass + 1))
fi

echo ""
echo "summary: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
