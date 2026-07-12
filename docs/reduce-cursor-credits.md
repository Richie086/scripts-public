# How to Reduce Cursor Credit and Token Usage

Cursor charges credits based on how much you use the model. In practice, that means **every token sent to and received from the model counts**—including conversation history, tool results, rules, skills, and MCP server definitions. The context window (often 200K tokens on recent models) is both a hard limit and a cost driver: the fuller your context, the more you pay on each new message.

This guide is based on a real context-usage breakdown from a long agent chat (~156K of 200K tokens used). The numbers below come from that session and illustrate where savings actually come from.

---

## How Credits Relate to Context and Tokens

Think of each agent turn as shipping a package to the model. The package includes:

1. **Your latest message**
2. **The full conversation so far** (prior turns, assistant replies, tool calls, tool results)
3. **Static overhead** re-sent every turn: system prompt, tool schemas, user rules, skills, MCP definitions, subagent metadata

Credits are consumed in proportion to that total payload. You cannot shrink tool definitions (~8K tokens, managed by Cursor), but you *can* control how much history accumulates and how large your per-turn overhead is.

| Category | Typical role | User-configurable? |
|----------|--------------|-------------------|
| Conversation history | Past turns + tool results | Yes — start new chats, avoid marathon sessions |
| Tool results (StrReplace, Shell, Read) | File diffs, command output, file contents | Partially — workflow choices |
| Skills (plugin + user) | Domain instructions injected each turn | Yes — disable plugins, `disable-model-invocation` |
| MCP servers | Tool schemas + server instructions | Yes — disable unused servers |
| User rules | Standing instructions | Yes — trim in Settings |
| Tool definitions | Built-in agent tools | No |

---

## Highest Impact: Start New Chats

In the analyzed session, **88% of context (~137K tokens) was conversation history**. That dwarfs everything else.

Long editing sessions are the main culprit. A single chat that grows to 13 turns can retain:

- Large `StrReplace` payloads (full `old_string` / `new_string` pairs for big files)
- Verbose `Shell` output from dozens of commands
- Exploration reads from early turns that are no longer relevant

**Actionable advice:**

- **Start a fresh chat when you change tasks.** Finished the README? Open a new chat for the next feature. You keep the same rules, skills, and tools; you drop accumulated history.
- **Avoid “one chat for the whole project.”** Multi-file refactors, debugging marathons, and README + code + CI work in one thread compound quickly.
- **Split by scope.** One chat for “add mermaid diagram,” another for “fix CI,” another for “refactor script X.”

**Estimated savings:** Starting fresh after a heavy session can reclaim **~85–117K tokens** immediately (roughly 60–75% of a full 200K window). This is the single largest lever.

---

## Reduce Per-Turn Overhead

Even before conversation history grows, every turn pays a **static baseline**. In the analyzed chat, that baseline was **~18.6K tokens per turn**:

| Component | Tokens/turn (approx.) | Notes |
|-----------|----------------------|-------|
| Tool definitions | ~8.1K | Not user-configurable |
| AWS plugin skills (23) | ~2.9K | Disable if not doing AWS work |
| User rules | ~3.0K | Trim verbose rules |
| cursor-ide-browser MCP | ~1.3K | Disable when not automating the browser |
| Subagents | ~811 | Lower priority |
| cursor-app-control MCP | ~667 | Keep if you use Canvas/automation |
| AWS MCP plugins | ~84 | Small; disable with AWS plugins |

Trimming overhead saves tokens **on every turn**, which adds up fast in a 20-turn session.

### Disable unused MCP servers

MCP servers inject tool schemas and often long server-use instructions into every turn.

**Recommended (global):**

1. Open **Cursor Settings → MCP** (or edit `~/.cursor/mcp.json` on Linux).
2. **Disable `cursor-ide-browser`** when you are not doing web automation, scraping, or browser-based testing. Saves **~1.3K tokens/turn**.
3. **Disable AWS MCP servers** (`plugin-aws-agents-awsknowledge`, `plugin-aws-core-aws-mcp`) if you are not on AWS work. Saves **~84 tokens/turn** (small alone, but pairs with plugin skills).
4. Keep **`cursor-app-control`** only if you rely on Canvas, automations, or app-control tools (~667 tokens/turn).

Example `~/.cursor/mcp.json` with browser disabled:

```json
{
  "mcpServers": {
    "cursor-ide-browser": {
      "disabled": true
    }
  }
}
```

Exact schema may vary by Cursor version; the Settings UI is the most reliable path. Restart or reload Cursor after changes.

> **Verification note:** As of writing this guide, `~/.cursor/mcp.json` was not present on this machine—MCP servers were likely enabled via the Cursor UI or bundled plugins. The recommendations above are what a sibling config task targeted; apply them manually if not already done.

### Disable AWS and other unused plugins

The AWS Core and AWS Agents plugins inject **23 skill files (~2.9K tokens/turn)** even when your task has nothing to do with AWS.

**Recommended:**

1. Open **Cursor Settings → Plugins** (or the plugin marketplace manage view).
2. **Disable `aws-core` and `aws-agents`** globally if you rarely work on AWS.
3. Disable any other plugins whose skills you never trigger (e.g. docs-canvas if you do not use Canvas docs).

Re-enable plugins when you need them; the token cost only applies while they are active.

### Use `disable-model-invocation` on skills

Skills listed in the agent’s available skills are summarized and injected each turn. For skills you only want when explicitly invoked (slash commands, manual `@skill`), add to the skill’s YAML frontmatter:

```yaml
---
name: my-skill
description: Short description for when the model may load it.
disable-model-invocation: true
---
```

With `disable-model-invocation: true`, the skill is **not** auto-injected every turn. The model can still use it when you explicitly reference it.

**For AWS plugin skills you cannot disable entirely:** editing cached plugin `SKILL.md` files under `~/.cursor/plugins/cache/` is possible but **fragile**—updates may overwrite your changes. Prefer disabling the plugin in Settings when you do not need AWS.

### Trim user rules

User rules cost **~3K tokens/turn** in the analyzed session. Rules are re-sent on every turn, so verbosity multiplies.

**Recommended:**

1. Open **Cursor Settings → Rules** (user rules apply globally).
2. Remove or shorten rules that duplicate what the model already does (long git essays, repeated formatting instructions).
3. Keep high-value, non-obvious rules: commit safety, PR workflow preferences, project-specific conventions.
4. Move rarely used instructions into **project rules** (`.cursor/rules/` in a repo) so they load only in that workspace—if your Cursor version scopes them that way.

**Estimated savings from trimming rules:** ~30% of rule tokens (~900 tokens/turn) if you cut redundant prose.

---

## Conversation Bloat: Tool Results Accumulate

Tool results stay in conversation history for the life of the chat. In the analyzed session:

| Tool | Approx. tokens retained | Calls |
|------|-------------------------|-------|
| StrReplace | ~67K | 35 |
| Shell | ~19K | 42 |
| Read / Write | (included in turn totals) | many |

### StrReplace

Each edit stores the full `old_string` and `new_string`. Multi-file refactors with large hunks dominate context. The heaviest turns (~39K and ~27K tokens) were editing sessions with many StrReplace calls.

**Reduce bloat:**

- Prefer **smaller, focused edits** over rewriting entire files in one replace when possible.
- **Start a new chat** after a large refactor instead of asking follow-ups in the same thread.
- For repetitive mechanical edits, consider a script or local tool instead of dozens of agent edits in one chat.

### Shell

Command output (build logs, `find`, `git log`, test runners) is retained verbatim.

**Reduce bloat:**

- Ask the agent to run **narrow commands** (`git status` vs. full test suite with verbose output).
- Pipe or limit output when appropriate (`head`, `--quiet`, targeted grep).
- After a debugging spree with noisy output, **start a new chat** for the next task.

### Read

Reading large files or many files in exploration adds content to history.

**Reduce bloat:**

- Point the agent at **specific files** rather than “explore the whole repo.”
- Use `@` file references in your message so the model loads only what you need.

---

## When Summarization Helps

Cursor may summarize older context when the window fills up. Summarization **helps you stay under the limit** but has tradeoffs:

- **Good when:** You must continue a long thread and losing fine-grained tool output from turn 3 is acceptable.
- **Bad when:** You need exact prior diffs, command output, or step-by-step debugging history.

**Practical guidance:**

- Do not rely on summarization as your primary savings strategy. **Starting a new chat** is more predictable.
- If summarization triggers, paste a **short recap** of decisions and open files into the new chat rather than continuing a degraded thread.
- For long-running work, keep a **local scratch note** (issue text, checklist, key file paths) you can paste into fresh chats cheaply.

---

## Global vs Project Configuration

Changes can apply everywhere or only in one repo. For credit savings that follow you across projects, prefer **user-level (global) config**.

| Location (Linux) | Scope | Use for |
|------------------|-------|---------|
| `~/.config/Cursor/User/settings.json` | Global | Editor and Cursor user settings |
| `~/.cursor/mcp.json` | Global | MCP server enable/disable |
| `~/.cursor/rules/` | Global | User rules (all projects) |
| `.cursor/rules/` in a repo | Project | Repo-specific rules only |
| `.vscode/settings.json` in a repo | Project | Workspace editor settings |
| Cursor Settings → Plugins | Global | Enable/disable plugins |

**Important:** User rules and global MCP settings apply **in every project**. That is what you want for baseline overhead reduction (disable browser MCP globally, disable AWS plugins globally).

Project rules make sense for repo-specific conventions without paying their token cost in unrelated repos—when Cursor scopes them correctly.

> - **Plugins:** run `bash scripts/apply-cursor-credit-savings.sh` (clears AWS plugin from all workspace scopes; supports `--help`, `--dry-run`, and `--database <path>`), or use **Cursor Settings → Plugins** to disable AWS Core / AI Agents on AWS
> - **MCP:** **Customize → MCP** → toggle off `cursor-ide-browser` when not browsing (~1.3K tokens/turn; no file-based global toggle today)
> - Reload the window afterward

---

## Quick Checklist

Use this before and during long agent sessions:

- [ ] **New task → new chat** (biggest win)
- [ ] **AWS plugins off** when not doing AWS (~2.9K/turn)
- [ ] **Browser MCP off** when not doing web automation (~1.3K/turn)
- [ ] **User rules reviewed** — remove redundancy (~up to 900/turn)
- [ ] **Avoid marathon edit sessions** in one chat (StrReplace bloat)
- [ ] **Limit noisy shell commands** or start fresh after debugging
- [ ] **Scoped prompts** with `@file` instead of broad exploration
- [ ] **`disable-model-invocation: true`** on rarely used custom skills

---

## Estimated Savings Summary

Figures are from one analyzed session and scale with your usage. “Per turn” savings apply to **every** message in a chat; “one-time” savings apply when you reset history.

| Action | Est. savings | Type |
|--------|--------------|------|
| Start new chat after heavy session | ~85–117K tokens | One-time (clears history) |
| Disable AWS plugins (23 skills) | ~2.9K tokens | Per turn |
| Disable cursor-ide-browser MCP | ~1.3K tokens | Per turn |
| Trim user rules (~30% reduction) | ~900 tokens | Per turn |
| Disable AWS MCP servers | ~84 tokens | Per turn |
| Avoid large multi-file StrReplace marathons | ~60K+ tokens | Over session (stays in history) |
| Reduce verbose Shell output | ~10–19K tokens | Over session |

**Example:** A 20-turn chat after trimming overhead saves roughly `(2.9K + 1.3K + 0.9K) × 20 ≈ 102K tokens` compared to the unoptimized baseline—**before** counting conversation history. Combined with starting fresh between tasks, total savings can be dramatic.

---

## Reload and Verify

After changing MCP, plugins, or rules:

1. **Reload Cursor** (Command Palette → “Developer: Reload Window”) or restart the app.
2. Open **Context Usage** (if available in your build) or start a short test chat and inspect the breakdown.
3. Confirm plugin skills and MCP entries you disabled no longer appear in the static overhead categories.

---

## Bottom Line

**Credits track tokens.** Conversation history is usually the largest cost; **new chats** are the highest-impact habit. **Per-turn overhead** (plugins, MCP, rules) is the second lever—worth fixing globally so every project benefits. Tool result bloat from StrReplace and Shell is session-specific; split work across chats or narrow commands rather than carrying a whole refactor in one thread.

Apply the global config recommendations once, adopt the chat hygiene habits ongoing, and re-check context usage occasionally to see what dominates your sessions.
