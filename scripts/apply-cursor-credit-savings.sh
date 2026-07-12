#!/usr/bin/env bash
# Apply global Cursor credit-saving settings on Linux.
# Disables the AWS marketplace plugin (plugin id 6306) across all workspaces.
# Estimated savings: ~2.9K tokens/turn from AWS skills + ~84 tokens from AWS MCPs.
#
# MCP toggles (browser, app-control) must still be done in Cursor UI — see docs/reduce-cursor-credits.md.

set -euo pipefail

STATE_DB="${HOME}/.config/Cursor/User/globalStorage/state.vscdb"
DRY_RUN=false

show_help() {
	cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Apply global Cursor credit-saving settings on Linux by clearing installed
plugins (such as the AWS marketplace plugin 6306) across all workspace scopes.

Options:
  -h, --help                 Show this help message and exit
  -d, --database PATH        Path to the Cursor state database
                             (default: ~/.config/Cursor/User/globalStorage/state.vscdb)
  -n, --dry-run              Show changes without writing to database or creating backups
EOF
}

# Parse options
while [[ $# -gt 0 ]]; do
	case "$1" in
		-h|--help)
			show_help
			exit 0
			;;
		-d|--database)
			if [[ -z "${2:-}" ]]; then
				echo "Error: --database requires a value." >&2
				exit 1
			fi
			STATE_DB="$2"
			shift 2
			;;
		-n|--dry-run)
			DRY_RUN=true
			shift
			;;
		*)
			echo "Error: Unknown argument: $1" >&2
			show_help >&2
			exit 1
			;;
	esac
done

if [[ ! -f "${STATE_DB}" ]]; then
	echo "Cursor state database not found: ${STATE_DB}" >&2
	exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
	echo "python3 is required" >&2
	exit 1
fi

if [ "$DRY_RUN" = false ]; then
	BACKUP="${STATE_DB}.backup-$(date +%Y%m%d-%H%M%S)"
	cp "${STATE_DB}" "${BACKUP}"
	echo "Backed up state DB to: ${BACKUP}"
fi

python3 - "$STATE_DB" "$DRY_RUN" <<'PY'
import sqlite3
import sys

db_path = sys.argv[1]
dry_run = sys.argv[2].lower() == 'true'

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Verify that ItemTable exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ItemTable'")
if not cur.fetchone():
    print("Error: ItemTable table not found in database.", file=sys.stderr)
    conn.close()
    sys.exit(1)

cur.execute(
    "SELECT key, value FROM ItemTable WHERE key LIKE 'cursor.plugins.installedIds.%'"
)
rows = cur.fetchall()

if not rows:
    print("No plugin install keys found — nothing to change.")
else:
    for key, value in rows:
        print(f"Key: {key}")
        print(f"  Before: {value if value else '(missing)'}")
        if dry_run:
            print("  After:  [] (dry-run, not written)")
        else:
            cur.execute("UPDATE ItemTable SET value=? WHERE key=?", ("[]", key))
            if cur.rowcount == 0:
                cur.execute(
                    "INSERT INTO ItemTable (key, value) VALUES (?, ?)", (key, "[]")
                )
            print("  After:  []")
            
    if not dry_run:
        conn.commit()
        print(f"Cleared installed plugins on {len(rows)} scope(s).")
    else:
        print(f"Dry run complete. Would have modified {len(rows)} scope(s).")

conn.close()
PY

if [ "$DRY_RUN" = false ]; then
	cat <<'EOF'

Done. Next steps:
  1. Quit and reopen Cursor (or Developer: Reload Window).
  2. In Customize → MCP, disable cursor-ide-browser when not doing web work (~1.3K/turn).
  3. Re-enable AWS plugins in Customize → Plugins only when you need them.

See docs/reduce-cursor-credits.md for the full checklist.
EOF
fi
