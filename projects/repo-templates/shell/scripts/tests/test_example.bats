#!/usr/bin/env bats

setup() {
  # Locate the script under test relative to the test file location
  DIR="$( cd "$( dirname "$BATS_TEST_FILENAME" )" >/dev/null 2>&1 && pwd )"
  SCRIPT="$DIR/../bash/example.sh"
}

@test "help flag returns 0 and outputs usage" {
  run "$SCRIPT" --help
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Usage:" ]]
}

@test "custom host flag sets host correctly" {
  run "$SCRIPT" --host 192.168.1.1
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Target host configured as: 192.168.1.1" ]]
}

@test "unknown flag returns 1" {
  run "$SCRIPT" --unknown-flag-test
  [ "$status" -eq 1 ]
}
