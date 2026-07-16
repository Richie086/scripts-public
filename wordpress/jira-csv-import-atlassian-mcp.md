# When Jira’s CSV Importer Fails, Paste the Spreadsheet Into Chat and Walk Away

I spent part of today trying to do something that sounds simple on paper: take a backlog I had already organized in a CSV and bulk-import it into Jira Cloud. Three projects. Parent tasks. Subtasks. Descriptions. The whole nine yards.

How hard could it be?

Famous last words.

## The Mission

I had roughly a day’s worth of planning sitting in a spreadsheet with columns for project, issue type, summary, description, and parent task. The plan was to shove all of it into Jira across three separate projects on my `errorcodezero.atlassian.net` site:

- **ES** — Extreme Sarcasm stuff (CLI tooling, WordPress automation, content work)
- **EXIT** — Exit Code Zero infrastructure (Hetzner migrations, GitLab, analytics scripts, the usual self-hosting chaos)
- **IF** — Idea Forge application work (admin UI, AI workflows, bug fixes, feature breakdowns)

Parent rows were **Tasks**. Child rows were **Sub-tasks** — things like “Implement Facebook auto-poster” hanging under a parent like `CLI: Anti-gravity CLI Social Media Auto-Poster`.

Reasonable structure. Clean data. Projects already created in Jira. Project keys already matched.

Jira, naturally, had other ideas.

## Round One: The Official CSV Import (a.k.a. Why Are You Like This)

I went straight for Jira’s built-in **Import CSV** flow in the web UI because that is what a reasonable human being would try first.

The projects existed. The keys in my CSV — `ES`, `EXIT`, `IF` — matched what Jira showed in project settings. I triple-checked. I am not above triple-checking when software is involved.

It still failed. Repeatedly. The errors kept circling back to two fields:

### Project

The importer acted like it could not resolve the **Project** column even though the keys were correct. Not the project *names*. The keys. The short codes. The thing Jira itself prints on every ticket.

If you have ever fought a CSV import, you know this vibe. One invisible space, one casing mismatch, one column mapped wrong in the UI, and suddenly Jira is telling you the project does not exist while you are literally staring at the project in another browser tab.

These are **team-managed** (next-gen) projects, which means configuration is scoped per project instead of using the older global scheme model. That does not make the importer any more patient.

### Issue Type

This was the real killer.

My CSV used `Sub-task` — with a hyphen — because that is what most spreadsheets, exports, and templates use. Perfectly normal.

Jira Cloud on my site wanted **`Subtask`**. No hyphen. Team-managed work type. Project-scoped. Very particular about spelling, apparently.

`Task` rows were fine. `Sub-task` rows were not. And when the importer cannot map an issue type, it does not always tell you *why* in a way that saves you any time. It just fails the row and leaves you to play CSV detective.

On top of that, the web importer is not great when you also have:

- Parent/child relationships that need to resolve by summary text
- Multiline descriptions in quoted CSV cells
- Subtasks that cannot exist until their parent tasks already do

So yes — correct project keys and still dead in the water. Love that for me.

## Round Two: Stop Fighting the UI, Start Talking to the API (Through Chat)

At this point I did what any sysadmin who is tired of clicking through failure dialogs would do: I stopped trying to make the web importer happy and opened **Cursor** with the **Atlassian plugin** installed.

That plugin wires up an **Atlassian MCP server** — basically authenticated API access to Jira Cloud, callable from chat — plus skills for backlog work, triage, and related chores. Less “configure a script,” more “paste the problem and let the machine sort it.”

Which is, if we are being honest, the entire point of this blog.

### What I actually did

1. Authenticated the Atlassian MCP against my Jira Cloud site.
2. Pasted the CSV contents directly into chat. No file hosting. No import wizard. No ceremonial sacrifice to the CSV mapping screen.
3. Told it to import the rows as new issues across `ES`, `EXIT`, and `IF`.

That was it. That was the whole workflow from my side.

### What the agent figured out without me hand-holding it

It pulled live project metadata from Jira and compared it to my pasted data. Then it did the thing I had been manually failing to do all afternoon:

| What my CSV said | What Jira actually wanted | Fix |
|------------------|---------------------------|-----|
| `Sub-task` | `Subtask` | Map before create |
| `Task` | `Task` | Leave alone |
| `ES` / `EXIT` / `IF` | Same keys | Confirmed via API |

More importantly, it imported in the **right order**:

```text
Parse CSV → create all Task rows → map summary to issue key → create Subtasks with parent keys
```

Parents first. Children second. The way any sane human would structure it if the import tool gave you that option.

Example: it created `CLI: Anti-gravity CLI Social Media Auto-Poster` as **ES-1**, remembered that mapping, then attached subtasks like “Implement Facebook auto-poster” underneath it with the correct parent key.

No spreadsheet surgery. No re-upload loop. No quiet rage.

## The Scoreboard

**48 issues created. Zero failures.**

| Project | Tasks | Subtasks | Total |
|---------|-------|----------|-------|
| ES | 4 | 10 | 14 |
| EXIT | 9 | 4 | 13 |
| IF | 7 | 14 | 21 |
| **All** | **20** | **28** | **48** |

A few examples so you know this was not theoretical:

- **ES-1** — CLI: Anti-gravity CLI Social Media Auto-Poster (with ES-5 through ES-9 hanging off it)
- **ES-2** — CLI: WordPress Post Automation Enhancements
- **EXIT-1** — INFRA: Migrate exitcode.net to Hetzner
- **EXIT-8** — INFRA: Architect and Deploy Backend Dev Infrastructure & Virtualization Environment
- **IF-1** — APP: Refactor Admin Settings UI & Provider Config
- **IF-4** — BUG: Fix Collections Page '0 Entries' Issue

All of them landed in **To Do**, which is exactly where a freshly imported backlog should live before reality sets in.

## Why This Worked When the Web UI Did Not

The MCP is not cheating. It is still creating issues through Jira Cloud’s API. The difference is that chat adds a translation layer on top:

- It reads your site’s **actual** work types instead of assuming your CSV labels are gospel
- It creates parents before children instead of hoping the importer guesses correctly
- It handles multiline descriptions without breaking quoted CSV cells
- It tells you what got created — issue keys and all — instead of handing you a vague row failure

In other words: same destination, fewer broken tools along the way.

## Lessons I Should Not Have Had to Learn the Hard Way

1. **Matching project keys is necessary but not sufficient.** If another column is wrong, Jira will still reject the import like you personally insulted it.
2. **`Sub-task` and `Subtask` are not the same thing** on team-managed Jira Cloud projects. Check **Project settings → Work types** and stop trusting export templates.
3. **Hierarchical imports need two passes** — parents first, subtasks second with real issue keys.
4. **Pasting CSV into an MCP-enabled chat session** beats debugging the web importer when you have dozens of rows across multiple projects.
5. **Do not run the import twice unless you want duplicates.** This was create-only. Jira will happily make twins.

## If You Want to Steal My CSV Format

This is the structure that finally worked:

```csv
Project,Issue Type,Summary,Description,Parent
ES,Task,CLI: Anti-gravity CLI Social Media Auto-Poster,,
ES,Sub-task,Implement Facebook auto-poster,Integrate API call...,CLI: Anti-gravity CLI Social Media Auto-Poster
EXIT,Task,INFRA: Migrate exitcode.net to Hetzner,,
IF,Task,APP: Refactor Admin Settings UI & Provider Config,,
```

The agent mapped `Sub-task` → `Subtask` at import time and converted parent summaries into real issue keys after the parent tasks existed.

If you are keeping CSV as a source of truth going forward, standardize on `Subtask` in the sheet and save yourself the grief.

## The Moral of the Story

Jira’s CSV importer choked on **Project** and **Issue Type** validation even though the projects were already there and the keys matched. The real problem was a team-managed naming mismatch — `Sub-task` vs `Subtask` — plus the importer’s general inability to gracefully handle parent/child creation order.

So I pasted the whole CSV into Cursor, let the Atlassian MCP authenticate to Jira Cloud, and watched it normalize the data, create 20 parent tasks and 28 subtasks in the right order, and hand back links to every issue.

Another afternoon task offloaded to the machines so I can look organized while they do the heavy lifting.
