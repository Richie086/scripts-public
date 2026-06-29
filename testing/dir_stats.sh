#!/bin/bash

# Target directory to analyze (default: current directory)
TARGET_DIR="${1:-.}"

if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' does not exist." >&2
    exit 1
fi

# Clean up path to absolute path
ABS_TARGET_DIR=$(cd "$TARGET_DIR" && pwd)

# Output file path (writes to the directory where the script is run)
OUTPUT_FILE="directory_stats.md"

# Detect and use the correct find utility (avoiding Windows find.exe on Windows)
if [ -x "/usr/bin/find" ]; then
    FIND="/usr/bin/find"
elif [ -x "/bin/find" ]; then
    FIND="/bin/find"
else
    FIND="find"
fi

# Calculate counts
# 1. Total Files (excluding directories)
TOTAL_FILES=$("$FIND" "$ABS_TARGET_DIR" -type f | wc -l)

# 2. Top-level folders
TOP_LEVEL_FOLDERS=$("$FIND" "$ABS_TARGET_DIR" -maxdepth 1 -type d | grep -v -e "^$ABS_TARGET_DIR$" | wc -l)

# 3. Total subfolders (recursive, excluding the root target dir)
TOTAL_SUBFOLDERS=$("$FIND" "$ABS_TARGET_DIR" -type d | grep -v -e "^$ABS_TARGET_DIR$" | wc -l)

# 4. Total size of the folder
TOTAL_SIZE=$(du -sh "$ABS_TARGET_DIR" 2>/dev/null | cut -f1)

# Generate Markdown Content
MARKDOWN_OUTPUT=$(cat <<EOF
# Directory Statistics Report

- **Target Directory:** \`$ABS_TARGET_DIR\`
- **Date/Time:** $(date)

## Overview

| Metric | Count / Size |
| :--- | :--- |
| **Total Files** | $TOTAL_FILES |
| **Top-Level Folders** | $TOP_LEVEL_FOLDERS |
| **Total Subfolders (Recursive)** | $TOTAL_SUBFOLDERS |
| **Total Folder Size** | $TOTAL_SIZE |
EOF
)

# Output to file
echo "$MARKDOWN_OUTPUT" > "$OUTPUT_FILE"

# Output to stdout
echo "$MARKDOWN_OUTPUT"
