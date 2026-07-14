#!/usr/bin/env bash
set -euo pipefail

: "${ATLASSIAN_API_TOKEN:?Set ATLASSIAN_API_TOKEN in your env}"

JIRA_URL="https://errorcodezero.atlassian.net"
EMAIL="richie086@gmail.com"

issues=(ES-16 ES-17 ES-18 ES-19 ES-20 ES-21 ES-22 ES-23 ES-24 ES-25)
labels=(git github repositories consolidation)

label_json=$(printf '"%s",' "${labels[@]}")
label_json="[${label_json%,}]"

for issue in "${issues[@]}"; do
  curl -sf -u "${EMAIL}:${ATLASSIAN_API_TOKEN}" \
    -X PUT \
    -H "Content-Type: application/json" \
    "${JIRA_URL}/rest/api/3/issue/${issue}" \
    -d "{\"fields\": {\"labels\": ${label_json}}}"
  echo "Tagged ${issue}"
done
