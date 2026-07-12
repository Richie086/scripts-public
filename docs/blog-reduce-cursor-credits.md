# Stop Burning Cursor Credits on Context You Don't Need

**If your agent chats feel slow, expensive, or mysteriously "full," the culprit is usually not your latest prompt—it's everything else riding along with it.**

Cursor charges credits based on token usage. Every message you send ships a package to the model: your words, the entire conversation so far, tool outputs, user rules, plugin skills, MCP server definitions, and subagent metadata. On a 200K context window, that package gets heavy fast—and the fuller your context, the more you pay on each new message.

I analyzed a real long agent session that had consumed **~156K of 200K tokens**. The breakdown was revealing—and the fixes are more practical than you might expect. This post turns that analysis into habits and settings you can apply today.

---

## Every Turn Ships the Whole Conversation

Think of each agent turn as FedEx for tokens. The box always includes:

1. Your latest message
2. **Full conversation history** (prior turns, replies, tool calls, tool results)
3. **Static overhead** re-sent every turn: system prompt, tool schemas, user rules, skills, MCP definitions, subagent metadata

You cannot shrink built-in tool definitions (~8K tokens, managed by Cursor). You *can* control how much history piles up and how bloated your per-turn baseline is.

| Category | What it does | Can you change it? |
|----------|--------------|-------------------|
| Conversation history | Past turns + tool results | Yes — new chats, shorter sessions |
| Tool results (StrReplace, Shell, Read) | Diffs, command output, file contents | Partially — workflow choices |
| Skills (plugin + user) | Domain instructions each turn | Yes — disable plugins, opt-out flags |
| MCP servers | Tool schemas + server instructions | Yes — disable unused servers |
| User rules | Standing instructions | Yes — trim in Settings |
| Tool definitions | Built-in agent tools | No |

The takeaway: **two levers matter most**—conversation history (session habit) and per-turn overhead (one-time global config).

---

## Lever 1: Start a New Chat (The Biggest Win)

In the analyzed session, **88% of context—about 137K tokens—was conversation history**. Everything else was noise by comparison.

Long editing sessions are the main culprit. A 13-turn chat can retain:

- Large `StrReplace` payloads (full before/after strings for big files)
- Verbose `Shell` output from dozens of commands
- Exploration reads from early turns you no longer need

### What to do instead

- **New task → new chat.** Finished the README? Open a fresh chat for the next feature. You keep rules, skills, and tools; you drop accumulated history.
- **Avoid "one chat for the whole project."** Multi-file refactors, debugging marathons, and README + code + CI in one thread compound quickly.
- **Split by scope.** One chat for the diagram, another for CI, another for the refactor.

**Estimated savings:** Starting fresh after a heavy session can reclaim **~85–117K tokens** immediately—roughly **60–75% of a full 200K window**. This is the single largest lever. No settings change required.

---

## Lever 2: Trim Your Per-Turn Overhead

Before conversation history even grows, every turn pays a static baseline. In the analyzed chat, that baseline was **~18.6K tokens per turn**:

| Component | Tokens/turn (approx.) | Action |
|-----------|----------------------|--------|
| Tool definitions | ~8.1K | Not configurable |
| AWS plugin skills (23) | ~2.9K | Disable if not doing AWS |
| User rules | ~3.0K | Trim verbose rules |
| cursor-ide-browser MCP | ~1.3K | Disable when not browsing |
| Subagents | ~811 | Lower priority |
| cursor-app-control MCP | ~667 | Keep if you use Canvas/automation |
| AWS MCP plugins | ~84 | Disable with AWS plugins |

Trimming overhead saves tokens **on every turn**. In a 20-turn chat, small per-turn wins become large session wins.

### Disable unused MCP servers

MCP servers inject tool schemas and often long server-use instructions into every turn.

1. Open **Cursor Settings → MCP** (or edit `~/.cursor/mcp.json` on Linux).
2. **Disable `cursor-ide-browser`** when you are not doing web automation, scraping, or browser-based testing. Saves **~1.3K tokens/turn**.
3. **Disable AWS MCP servers** (`plugin-aws-agents-awsknowledge`, `plugin-aws-core-aws-mcp`) if you are not on AWS work. Saves **~84 tokens/turn** (small alone, but pairs with plugin savings).
4. Keep **`cursor-app-control`** only if you rely on Canvas, automations, or app-control tools (~667 tokens/turn).

Example config with browser disabled:

```json
{
  "mcpServers": {
    "cursor-ide-browser": {
      "disabled": true
    }
  }
}
```

Reload Cursor after changes. The Settings UI is the most reliable path if the file schema varies by version—and on some setups, `~/.cursor/mcp.json` may not exist at all; MCP servers are enabled via the UI or bundled plugins instead.

### Disable unused plugins

The AWS Core and AWS Agents plugins inject **23 skill files (~2.9K tokens/turn)** even when your task has nothing to do with AWS.

1. Open **Cursor Settings → Plugins** (or the plugin marketplace manage view).
2. **Disable `aws-core` and `aws-agents`** globally if you rarely work on AWS.
3. Disable other plugins whose skills you never trigger—e.g. docs-canvas if you do not use Canvas docs.

Re-enable when you need them. The cost only applies while they are active.

### Opt out of auto-injected skills

For skills you only want when explicitly invoked, add to the skill's YAML frontmatter:

```yaml
---
name: my-skill
description: Short description for when the model may load it.
disable-model-invocation: true
---
```

With `disable-model-invocation: true`, the skill is **not** auto-injected every turn. The model can still use it when you reference it directly.

**Heads up for AWS plugin skills:** editing cached plugin `SKILL.md` files under `~/.cursor/plugins/cache/` is possible but fragile—updates may overwrite your changes. Prefer disabling the plugin in Settings when you do not need AWS.

### Trim user rules

User rules cost **~3K tokens/turn** in the analyzed session—and they are re-sent on **every** turn, so verbosity multiplies.

1. Open **Cursor Settings → Rules**.
2. Remove rules that duplicate what the model already does (long git essays, repeated formatting instructions).
3. Keep high-value, non-obvious rules: commit safety, PR workflow preferences, project-specific conventions.
4. Move rarely used instructions into **project rules** (`.cursor/rules/` in a repo) so they load only in that workspace—if your Cursor version scopes them that way.

**Estimated savings from trimming rules:** ~30% of rule tokens (~**900 tokens/turn**) if you cut redundant prose.

---

## Watch Out for Tool Result Bloat

Tool results stay in conversation history for the life of the chat. In the analyzed session:

| Tool | Approx. tokens retained | Calls |
|------|-------------------------|-------|
| StrReplace | ~67K | 35 |
| Shell | ~19K | 42 |
| Read / Write | (included in turn totals) | many |

### StrReplace

Each edit stores the full `old_string` and `new_string`. Multi-file refactors with large hunks dominate context—the heaviest turns (~39K and ~27K tokens) were editing marathons.

- Prefer **smaller, focused edits** over rewriting entire files in one replace.
- **Start a new chat** after a large refactor.
- For repetitive mechanical edits, use a script instead of dozens of agent edits in one chat.

### Shell

Command output (build logs, `find`, `git log`, test runners) is retained verbatim.

- Ask for **narrow commands** (`git status` vs. a full verbose test suite).
- Pipe or limit output (`head`, `--quiet`, targeted grep).
- After a noisy debugging spree, **start a new chat** for the next task.

### Read

- Point the agent at **specific files** rather than "explore the whole repo."
- Use `@` file references so the model loads only what you need.

---

## Don't Rely on Summarization Alone

Cursor may summarize older context when the window fills up. That helps you stay under the limit, but it has tradeoffs:

- **Good when:** You must continue a long thread and losing fine-grained tool output from early turns is acceptable.
- **Bad when:** You need exact prior diffs, command output, or step-by-step debugging history.

**Better approach:** Treat summarization as a fallback, not a strategy. Starting a new chat is more predictable. If summarization does trigger, paste a **short recap** of decisions and open files into the new chat rather than continuing a degraded thread. For long-running work, keep a **local scratch note** (decisions, checklist, key file paths) you can paste into fresh chats cheaply.

---

## Configure Once, Save Everywhere

For credit savings that follow you across projects, prefer **global (user-level) config**:

| Location (Linux) | Scope | Use for |
|------------------|-------|---------|
| `~/.config/Cursor/User/settings.json` | Global | Editor and Cursor user settings |
| `~/.cursor/mcp.json` | Global | MCP enable/disable |
| `~/.cursor/rules/` | Global | User rules (all projects) |
| `.cursor/rules/` in a repo | Project | Repo-specific rules only |
| `.vscode/settings.json` in a repo | Project | Workspace editor settings |
| Cursor Settings → Plugins | Global | Enable/disable plugins |

User rules and global MCP settings apply **in every project**—exactly what you want for baseline overhead reduction (disable browser MCP globally, disable AWS plugins globally). Project rules make sense for repo-specific conventions without paying their token cost in unrelated repos—when Cursor scopes them correctly.

**Verified on the machine where this analysis was run:** `~/.config/Cursor/User/settings.json` contained only display preferences. AWS plugin id `6306` was installed globally via `state.vscdb`. Browser MCP (`cursor-ide-browser`) was enabled by default. To apply reductions globally:

- **Plugins:** run `bash scripts/apply-cursor-credit-savings.sh` (clears AWS plugin from all workspace scopes; supports `--help`, `--dry-run`, and `--database <path>`), or disable AWS Core / AI Agents on AWS in **Cursor Settings → Plugins**
- **MCP:** **Customize → MCP** → toggle off `cursor-ide-browser` when not browsing (~1.3K tokens/turn; no file-based global toggle on this setup)
- Reload the window afterward

---

## Your Pre-Session Checklist

Before a long agent session, run through this:

- [ ] **New task → new chat** (biggest win)
- [ ] **AWS plugins off** when not doing AWS (~2.9K/turn)
- [ ] **Browser MCP off** when not doing web automation (~1.3K/turn)
- [ ] **User rules reviewed** — remove redundancy (~up to 900/turn)
- [ ] **Avoid marathon edit sessions** in one chat (StrReplace bloat)
- [ ] **Limit noisy shell commands** or start fresh after debugging
- [ ] **Scoped prompts** with `@file` instead of broad exploration
- [ ] **`disable-model-invocation: true`** on rarely used custom skills

---

## How Much Can You Actually Save?

Figures below come from one analyzed session and scale with your usage. "Per turn" savings apply to **every** message; "one-time" savings apply when you reset history.

| Action | Est. savings | Type |
|--------|--------------|------|
| Start new chat after heavy session | ~85–117K tokens | One-time |
| Disable AWS plugins (23 skills) | ~2.9K tokens | Per turn |
| Disable cursor-ide-browser MCP | ~1.3K tokens | Per turn |
| Trim user rules (~30% reduction) | ~900 tokens | Per turn |
| Disable AWS MCP servers | ~84 tokens | Per turn |
| Avoid large multi-file StrReplace marathons | ~60K+ tokens | Over session |
| Reduce verbose Shell output | ~10–19K tokens | Over session |

**Example:** A 20-turn chat after trimming overhead saves roughly `(2.9K + 1.3K + 0.9K) × 20 ≈ 102K tokens` compared to the unoptimized baseline—**before** counting conversation history. Combined with starting fresh between tasks, total savings can be dramatic.

---

## Verify Your Changes

After changing MCP, plugins, or rules:

1. **Reload Cursor** (Command Palette → "Developer: Reload Window") or restart the app.
2. Open **Context Usage** (if available in your build) or start a short test chat and inspect the breakdown.
3. Confirm disabled plugin skills and MCP entries no longer appear in static overhead.

---

## The Bottom Line

**Credits track tokens.** Conversation history is usually the largest cost—**new chats** are the highest-impact habit you can adopt today. **Per-turn overhead** (plugins, MCP, rules) is the second lever; fix it globally once so every project benefits. Tool result bloat from StrReplace and Shell is session-specific; split work across chats or narrow commands instead of carrying a whole refactor in one thread.

Apply the global config once. Adopt chat hygiene as an ongoing habit. Re-check context usage occasionally to see what dominates *your* sessions.

---

*Based on the technical guide at [`docs/reduce-cursor-credits.md`](reduce-cursor-credits.md).*
