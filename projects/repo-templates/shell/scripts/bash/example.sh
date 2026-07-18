#!/usr/bin/env bash
# Example template script demonstrating robust bash engineering standards.
set -euo pipefail

# Dynamic fallback variables (no hardcoded LAN IPs or credentials)
DEV_HOST="${DEV_HOST:-127.0.0.1}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

log() {
  local level="${1}"
  local msg="${2}"
  echo "[$(date +'%Y-%m-%dT%H:%M:%S')] [${level}] ${msg}" >&2
}

show_help() {
  cat <<EOF
Usage: $(basename "${0}") [options]

Options:
  -h, --help        Show this help message and exit.
  -d, --host HOST   Specify the host address (default: ${DEV_HOST}).
  -v, --verbose     Enable verbose debug logging.
EOF
}

# Parse command line options
VERBOSE=false
while [[ $# -gt 0 ]]; do
  case "${1}" in
    -h|--help)
      show_help
      exit 0
      ;;
    -d|--host)
      DEV_HOST="${2:?--host requires a value}"
      shift 2
      ;;
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    *)
      echo "Unknown option: ${1}" >&2
      show_help >&2
      exit 1
      ;;
  esac
done

if [ "$VERBOSE" = true ]; then
  LOG_LEVEL="DEBUG"
fi

log "${LOG_LEVEL}" "Starting example execution..."
log "INFO" "Target host configured as: ${DEV_HOST}"
log "INFO" "Task completed successfully!"
EOF
