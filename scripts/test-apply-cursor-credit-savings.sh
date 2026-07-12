#!/usr/bin/env bash
# Flag / logic tests for apply-cursor-credit-savings.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/apply-cursor-credit-savings.sh"
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

echo "==> apply-cursor-credit-savings.sh flag tests"
echo "    script: $SCRIPT"

# 1. Test --help
set +e
out="$(bash "$SCRIPT" --help 2>&1)"
ec=$?
set -e
assert_eq "--help exit 0" "0" "$ec"
assert_contains "--help shows Usage" "Usage: apply-cursor-credit-savings.sh" "$out"
assert_contains "--help lists --database" "--database" "$out"
assert_contains "--help lists --dry-run" "--dry-run" "$out"

# 2. Test -h
set +e
out="$(bash "$SCRIPT" -h 2>&1)"
ec=$?
set -e
assert_eq "-h exit 0" "0" "$ec"

# 3. Test Unknown flag
set +e
out="$(bash "$SCRIPT" --bogus 2>&1)"
ec=$?
set -e
assert_eq "unknown flag exit 1" "1" "$ec"
assert_contains "unknown flag message" "Unknown argument: --bogus" "$out"

# 4. Set up mock SQLite database for logical tests
TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT

TEST_DB="$TEST_DIR/test_state.vscdb"

# Create a valid mock database using python3
python3 -c "
import sqlite3
conn = sqlite3.connect('$TEST_DB')
cur = conn.cursor()
cur.execute('CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)')
cur.execute(\"INSERT INTO ItemTable (key, value) VALUES ('cursor.plugins.installedIds.work1', '[\\\"plugin-aws\\\"]')\")
cur.execute(\"INSERT INTO ItemTable (key, value) VALUES ('cursor.plugins.installedIds.work2', '[\\\"plugin-other\\\"]')\")
cur.execute(\"INSERT INTO ItemTable (key, value) VALUES ('other.key', 'some-value')\")
conn.commit()
conn.close()
"

# Test dry-run with mock DB
set +e
out="$(bash "$SCRIPT" --database "$TEST_DB" --dry-run 2>&1)"
ec=$?
set -e
assert_eq "dry-run exit 0" "0" "$ec"
assert_contains "dry-run prints expected output" "Dry run complete." "$out"
assert_contains "dry-run prints Key" "Key: cursor.plugins.installedIds.work1" "$out"

# Verify mock DB was NOT changed during dry-run
db_val1=$(python3 -c "
import sqlite3
conn = sqlite3.connect('$TEST_DB')
cur = conn.cursor()
cur.execute(\"SELECT value FROM ItemTable WHERE key='cursor.plugins.installedIds.work1'\")
print(cur.fetchone()[0])
conn.close()
")
assert_eq "dry-run did not change work1 value" "[\"plugin-aws\"]" "$db_val1"

# Verify NO backups were created
backup_count=$(find "$TEST_DIR" -name "*.backup-*" | wc -l)
assert_eq "dry-run created 0 backups" "0" "$backup_count"

# Test active execution with mock DB
set +e
out="$(bash "$SCRIPT" --database "$TEST_DB" 2>&1)"
ec=$?
set -e
assert_eq "run exit 0" "0" "$ec"
assert_contains "run prints cleared message" "Cleared installed plugins on 2 scope(s)" "$out"

# Verify mock DB WAS changed during active execution
db_val2=$(python3 -c "
import sqlite3
conn = sqlite3.connect('$TEST_DB')
cur = conn.cursor()
cur.execute(\"SELECT value FROM ItemTable WHERE key='cursor.plugins.installedIds.work1'\")
print(cur.fetchone()[0])
conn.close()
")
assert_eq "run changed work1 value to []" "[]" "$db_val2"

# Verify backups WERE created
backup_count2=$(find "$TEST_DIR" -name "*test_state.vscdb.backup-*" | wc -l)
assert_eq "run created 1 backup" "1" "$backup_count2"

echo ""
echo "summary: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
