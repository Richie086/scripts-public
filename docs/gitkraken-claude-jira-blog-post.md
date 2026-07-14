# Procedure: Connecting Claude, GitKraken, and Jira Cloud

## 1. Provision an Atlassian API token and MCP server config

1. Generate an API token from your Atlassian account (id.atlassian.com → Security → API tokens).
2. Do not paste the raw token into chat or commit it to a repo. Reference it via an environment variable instead.
3. Locate or create `.mcp.json` in the project root.
4. Add an `atlassian` entry under `mcpServers`, using `mcp-atlassian` and referencing the token by env var:
   ```json
   "atlassian": {
     "command": "uvx",
     "args": ["mcp-atlassian"],
     "env": {
       "JIRA_URL": "https://<your-site>.atlassian.net",
       "JIRA_USERNAME": "<your-email>",
       "JIRA_API_TOKEN": "${ATLASSIAN_API_TOKEN}"
     }
   }
   ```
5. Export the token in your shell profile (`~/.bashrc` / `~/.zshrc`):
   ```bash
   export ATLASSIAN_API_TOKEN="<token>"
   ```
6. Note: an interactive `!`-prefixed shell command and a separately spawned script/tool process do not share exported env vars. When running a script that needs the token, invoke it with `bash -lc '<script>'` so it sources the profile.

## 2. Create a Jira issue

1. Use a Jira-aware issue-creation tool (e.g. GitKraken's `issues_create`) with `provider: jira` and `repository_name: <PROJECT_KEY>`.
2. Confirm the returned issue key (e.g. `ES-16`).

## 3. Populate issue details from local state

1. Enumerate target data (e.g. `git remote -v` across all folders in a repos directory) to build a factual list.
2. If no "update description" tool is available, add the findings as an issue comment via a comment tool, or proceed to the REST API (step 4) to write the description field directly.

## 4. Update an issue via the Jira Cloud REST API directly

1. Base URL: `https://<your-site>.atlassian.net/rest/api/3/`
2. Auth: HTTP Basic with `<email>:<api-token>`.
3. The `description` field requires Atlassian Document Format (ADF) — a structured JSON doc tree, not markdown or plain text.
4. Example update:
   ```bash
   curl -u "$EMAIL:$ATLASSIAN_API_TOKEN" \
     -X PUT -H "Content-Type: application/json" \
     "https://<site>.atlassian.net/rest/api/3/issue/ES-16" \
     -d '{"fields": {"description": {"type":"doc","version":1,"content":[...]}}}'
   ```
5. Verify with the HTTP status code (`204` = success, no body).

## 5. Create subtasks

1. For each item to break out, `POST /rest/api/3/issue` with:
   ```json
   {
     "fields": {
       "project": {"key": "<PROJECT_KEY>"},
       "parent": {"key": "<PARENT_ISSUE>"},
       "summary": "<summary>",
       "issuetype": {"name": "Subtask"}
     }
   }
   ```
2. Loop over your item list, one request per subtask.

## 6. Apply labels in bulk

1. `PUT /rest/api/3/issue/<KEY>` with:
   ```json
   {"fields": {"labels": ["label-one", "label-two"]}}
   ```
2. Repeat for the parent issue and every subtask key.

## 7. Link an issue to a GitHub repository

- **Quick web link (any project):**
  ```bash
  curl -u "$EMAIL:$ATLASSIAN_API_TOKEN" \
    -X POST -H "Content-Type: application/json" \
    "https://<site>.atlassian.net/rest/api/3/issue/<KEY>/remotelink" \
    -d '{"object": {"url": "https://github.com/<org>/<repo>", "title": "<org>/<repo>"}}'
  ```
  This only appears under "Web Links" — no commit/PR/branch surfacing.

- **Real dev-panel integration (commits, branches, PRs on the issue):**
  1. Install the **GitHub for Jira** app from the Atlassian Marketplace (requires Jira org admin).
  2. Authorize via the interactive OAuth flow (requires a human in a browser — cannot be automated by an agent).
  3. Select the repositories to connect.
  4. Include the issue key (e.g. `ES-17`) in commit messages or branch names on the connected repo going forward.
  5. Once live, remove any redundant plain web link added in the interim (`DELETE /rest/api/3/issue/<KEY>/remotelink/<linkId>`).

## 8. Create new issue types (classic vs. team-managed projects)

1. Determine project type: `GET /rest/api/3/project/<KEY>` → check `style` (`classic` vs `next-gen`) and `projectTypeKey`.
2. Create the issue type site-wide:
   ```bash
   curl -u "$EMAIL:$ATLASSIAN_API_TOKEN" \
     -X POST -H "Content-Type: application/json" \
     "https://<site>.atlassian.net/rest/api/3/issuetype" \
     -d '{"name": "<TYPE_NAME>", "description": "<desc>", "type": "standard"}'
   ```
3. **Classic project:** attach it to the project's issue type scheme via `PUT /rest/api/3/issuetypescheme/<schemeId>`.
4. **Team-managed (next-gen) project:** the public REST API does not expose issue-type-scheme management for these. Attach manually: **Project settings → Issue types → Add issue type**, selecting the already-created type (don't recreate it).
5. Once attached, update individual issues' type via `PUT /rest/api/3/issue/<KEY>` with `{"fields": {"issuetype": {"name": "<TYPE_NAME>"}}}`.

## 9. Search issues via JQL (Jira Cloud API v3+)

1. The legacy `GET /rest/api/3/search` endpoint is deprecated/removed (`410`). Use `GET /rest/api/3/search/jql` instead.
2. Example:
   ```bash
   curl -u "$EMAIL:$ATLASSIAN_API_TOKEN" -G \
     "https://<site>.atlassian.net/rest/api/3/search/jql" \
     --data-urlencode "jql=project = <KEY>" \
     --data-urlencode "fields=summary" \
     --data-urlencode "maxResults=100"
   ```

## 10. Provision Confluence Cloud (if not already active on the site)

1. If `GET /wiki/rest/api/space` returns a 401/HTML error page instead of JSON, Confluence is not yet provisioned for the site.
2. Activate it via **admin.atlassian.com → Products → Add Confluence**.
3. Re-test with the same GET request; a proper JSON response confirms it's live.

## 11. Create a Confluence space

```bash
curl -u "$EMAIL:$ATLASSIAN_API_TOKEN" \
  -X POST -H "Content-Type: application/json" \
  "https://<site>.atlassian.net/wiki/rest/api/space" \
  -d '{"key": "<SPACEKEY>", "name": "<Space Name>"}'
```
Space key must be short, alphanumeric, no spaces.

## 12. Create a Confluence page with content

1. Confluence pages use **storage format** (XHTML-like), not raw markdown.
2. Convert markdown to storage format (headings, paragraphs, `<strong>`, `<code>` at minimum) before posting.
3. Create the page:
   ```bash
   curl -u "$EMAIL:$ATLASSIAN_API_TOKEN" \
     -X POST -H "Content-Type: application/json" \
     "https://<site>.atlassian.net/wiki/rest/api/content" \
     -d '{
       "type": "page",
       "title": "<Page Title>",
       "space": {"key": "<SPACEKEY>"},
       "body": {"storage": {"value": "<html>", "representation": "storage"}}
     }'
   ```
4. Verify by fetching it back:
   ```bash
   curl -u "$EMAIL:$ATLASSIAN_API_TOKEN" \
     "https://<site>.atlassian.net/wiki/rest/api/content/<pageId>?expand=body.storage,version"
   ```
5. Note: a page created via the API is not automatically linked from the space's homepage or sidebar tree. To make it discoverable, either set it as the space homepage or add it as a child page under the existing homepage.
