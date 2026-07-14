#!/usr/bin/env bash
set -euo pipefail

: "${ATLASSIAN_API_TOKEN:?Set ATLASSIAN_API_TOKEN in your env}"

JIRA_URL="https://errorcodezero.atlassian.net"
EMAIL="richie086@gmail.com"
ISSUE="ES-16"

curl -sf -u "${EMAIL}:${ATLASSIAN_API_TOKEN}" \
  -X PUT \
  -H "Content-Type: application/json" \
  "${JIRA_URL}/rest/api/3/issue/${ISSUE}" \
  -d @- <<'EOF'
{
  "fields": {
    "description": {
      "type": "doc",
      "version": 1,
      "content": [
        {
          "type": "paragraph",
          "content": [{"type": "text", "text": "Repos found in ~/repositories on this machine:"}]
        },
        {
          "type": "bulletList",
          "content": [
            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "AD-Ops — https://github.com/Richie086/AD-Ops.git"}]}]},
            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "antigravity-skills — https://github.com/rominirani/antigravity-skills.git (fork/third-party, not Richie086)"}]}]},
            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "EELLM — git@github.com:Richie086/EELLM.git"}]}]},
            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "exitcodezero — https://github.com/Richie086/exitcodezero.git"}]}]},
            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "scripts — git@github.com:Richie086/scripts.git"}]}]},
            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "scripts-public — git repo, no remote configured"}]}]},
            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "vscode-test — not a git repo"}]}]},
            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "wordpress-scraper — https://github.com/Richie086/wordpress-scraper.git"}]}]},
            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "worktrees — not a git repo (likely git worktree checkouts)"}]}]}
          ]
        }
      ]
    }
  }
}
EOF

echo "Updated ${ISSUE} description."
