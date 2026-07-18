#!/usr/bin/env bash
# Apply standard branch protection to main: require the gitleaks check,
# block force-pushes and deletions. Usage: ./protect-main.sh <repo-name>
set -euo pipefail

REPO_NAME="${1:?usage: protect-main.sh <repo-name>}"
OWNER="Richie086"

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
cat > "$TMP" <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["gitleaks"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null
}
EOF

gh api "repos/$OWNER/$REPO_NAME/branches/main/protection" -X PUT --input "$TMP" >/dev/null
echo "main protected on $OWNER/$REPO_NAME (gitleaks required, force-push/delete blocked)"
