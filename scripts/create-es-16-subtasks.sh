#!/usr/bin/env bash
set -euo pipefail

: "${ATLASSIAN_API_TOKEN:?Set ATLASSIAN_API_TOKEN in your env}"

JIRA_URL="https://errorcodezero.atlassian.net"
EMAIL="richie086@gmail.com"
PARENT="ES-16"
PROJECT_KEY="ES"

repos=(
  "AD-Ops|https://github.com/Richie086/AD-Ops.git"
  "antigravity-skills|https://github.com/rominirani/antigravity-skills.git (fork/third-party, not Richie086)"
  "EELLM|git@github.com:Richie086/EELLM.git"
  "exitcodezero|https://github.com/Richie086/exitcodezero.git"
  "scripts|git@github.com:Richie086/scripts.git"
  "scripts-public|no remote configured"
  "vscode-test|not a git repo"
  "wordpress-scraper|https://github.com/Richie086/wordpress-scraper.git"
  "worktrees|not a git repo (likely git worktree checkouts)"
)

for entry in "${repos[@]}"; do
  name="${entry%%|*}"
  detail="${entry#*|}"
  payload=$(cat <<EOF
{
  "fields": {
    "project": {"key": "${PROJECT_KEY}"},
    "parent": {"key": "${PARENT}"},
    "summary": "Organize repo: ${name}",
    "description": {
      "type": "doc",
      "version": 1,
      "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": "${detail}"}]}
      ]
    },
    "issuetype": {"name": "Subtask"}
  }
}
EOF
)
  result=$(curl -sf -u "${EMAIL}:${ATLASSIAN_API_TOKEN}" \
    -X POST \
    -H "Content-Type: application/json" \
    "${JIRA_URL}/rest/api/3/issue" \
    -d "${payload}")
  key=$(echo "$result" | grep -o '"key":"[^"]*"' | head -1 | cut -d'"' -f4)
  echo "Created ${key}: ${name}"
done
