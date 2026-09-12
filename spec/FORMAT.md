# Format contract

Everything trail does is defined by these files. The CLI is replaceable; the format
is the product.

## Layout

```
.trail/
  config.yml          optional; defaults apply when absent
  _template.md        task template, user-editable
  backlog.md          small items; a flat list, no frontmatter, no lifecycle
  tasks/<slug>.md     every task, open through done — files never move
```

`trail init` also drops `SKILL.md` where the repo's agents look for project skills:
`.claude/skills/trail/` for Claude Code, `.agents/skills/trail/` for Codex, Cursor and
Gemini CLI. There is no single path every agent reads.

trail keeps no second, repo-lifetime record. A decision log belongs to its task and
stays in its file, which is now permanent; four closes across two real repos produced
four untrimmed copies of the same content in a `DECISIONS.md` nobody ever distilled.
What deserves to outlive the task is a document the user asks for, under the repo's
own `docs/`, and that is theirs to decide — trail may point at the candidate, never
file it.

`.trail/` is committed by default. Solo users who want tasks off git add it to
`.gitignore`; the two-lifetime split survives either choice.

## Task file

```markdown
---
id: push-notification-deeplink
title: "push notification: deeplink"
level: T1
status: active
started: 2026-08-27
group: notifications
links:
  - src/Notifications/DeepLinkHandler.cs:120
---
# push notification deeplink

## Goal
## Plan
## Out of Scope
## Status
## Notes
## Decision Log
## Open Questions
```

The order is the reading order. A person opening this file asks "what is this, what
is left, where am I" — in that sequence, and the answer to each has to be above the
fold. Goal and Plan sit together because they are the same question at two
resolutions. `## Out of Scope` is a guardrail you consult, not a thing you act on, so
it follows them. The decision log is long and archival, so it sits below everything
you came for.

### Core fields

`id` · `title` · `level` · `status` · `group` are the only fields the CLI reads.
Everything else is free — add fields to `_template.md` and nothing breaks.

- `title` is **always written quoted**. Titles carry colons ("Report: pivot matrix")
  and a bare colon makes the whole block invalid YAML — which is how two of the five
  files in the first real ledger stopped opening in every other tool.

- `status` is one of `open` · `active` · `blocked` · `done`. The set is closed:
  board columns derive from it.
- `level` is `T1` or `T2`. T0 has no task file and no representation anywhere:
  small work being done now leaves no trace. `backlog.md` holds the other case,
  small work that is deferred.
- `group` is an optional slug shared by the tasks one `plan` run produced. It is a
  label, not a list of children: nothing points at anything, so nothing goes stale.
  `ls` sections by it, and anything reading frontmatter from outside — a Dataview
  query in an Obsidian vault, a script — can select on it.
- `links` is a flat list of repo paths, optionally `path:line`. Not validated.
  It is how a task points at the design document or the code it concerns.

There is still no parent task, no subtask, no dependency graph and no index file
listing children. `group` carries the only relation that survived contact with real
use: *these came from the same plan*.

### Plan items are checkboxes

```markdown
- [x] measure the run shape on device [completion:: 2026-09-11]
- [/] classify ErrorCode into messages
- [ ] overlap the loading phases
- [-] landscape mode — portrait-locked natively on both platforms
```

| | |
| --- | --- |
| `[ ]` | not started |
| `[/]` | written, not verified — the state that has no name in prose and therefore gets lost |
| `[x]` | verified. Not "I wrote it": verified. `[completion:: YYYY-MM-DD]` is Dataview's inline-field syntax and is optional everywhere else |
| `[-]` | cancelled — the item stays, with why it fell out of scope next to it |

This is the whole set. The next session reads the boxes instead of re-reading the
code, and the reader learns what is left without cross-referencing `## Status`
against a prose list. `ls` reports `verified / live` per task, where `[-]` leaves the
denominator — cancelled is resolved, not pending.

### Decision log entry

```markdown
- **2026-09-11** · fullscreen is a pushed page, not a modal
  - **why:** nothing in the repo uses PushModalAsync; a pushed page gets the
    hardware back button for free
  - **dropped:** the plan's "(modal)" note — a second navigation pattern with no
    precedent in the module
```

One scannable title line, the reasons indented under it. The old one-line form put
`why:` and `dropped:` inside a 600-character sentence, where finding either meant
reading all of it. `dropped:` is still the reason the format exists.

### `## Notes`

Free-form, append-only, dated by `trail note`. Nothing prescribes its shape.

It exists because the first real ledger pushed twenty-eight lines of measurements and
findings into the backlog for want of anywhere else to put them. A measurement is not
deferred work and it is not a decision; without a home it lands in whichever section
is nearest.

## What belongs in a task file

The task file is what every session starts by reading — through `trail status`, which
prints a digest of it rather than the file itself. Nothing is injected automatically;
trail ships no hook, on purpose. A session-start injection would put task context in
front of off-task work too, and the cure for a forgotten handoff is not poisoning
every unrelated session with it.

That constraint — read once per session, cheaply — is what divides the material:

| | Lives in | Read at session start |
| --- | --- | --- |
| What you must hold in your head each session — goal, boundary, position, decisions | the task file | yes, as a digest |
| What you consult when you reach that part — designs, specs, long plans | a reference document | no, linked |

`links:` is that bridge. A two-week design poured into `## Plan` breaks both halves:
the file stops answering "where am I", and the detail is re-read every session.

A reference document lives under the repo's own docs convention, never inside
`.trail/` — a different lifetime. trail links such a document; it does not own it.

Drift between the two is not a real risk, because they do not overlap: the document
holds the design and changes rarely, the task file holds the position and changes
constantly. A design change is one `trail log` line (why) plus a document edit (what
it now is).

## Splitting work across task files

**One task is the default.** Splitting is the exception and it has to be argued for.

The test is not size and not phase count:

> When you sit down to phase 3, do you need phase 1's status and decisions in your
> head?

- **Yes** → one T2 task, phases as checkboxes under `## Plan`. Ten phases still
  means one file: splitting it splits the context you were trying to carry.
- **No** → separate tasks.

The first real use split one report module into five tasks and failed this test in
writing: each file's `## Out of Scope` pointed at the others by name. What actually
drove the split was the source document's phase headings — **a document's sections
are not task boundaries.** A plan document is organised for reading; a ledger is
organised around what has to be in your head at once.

When you do split, order still lives in the slug prefix (`auth-1-provider`,
`auth-2-session`) — tasks sort by `(status, id)`, so the prefix carries it for free —
and the relation lives in `group:`. Still no `after:`, no parent, no subtask, no
index file listing children: a hand-written cross-reference goes stale within the
hour, while a shared label cannot.

## Template placeholders

`trail start` substitutes `{{id}}` `{{title}}` `{{level}}` `{{status}}` `{{date}}`.
**Unrecognized placeholders are left untouched**, so custom fields are safe.

## Config

Flat YAML. Keys: `backlog` `dir` `decisions` `template` `stale_days`. Unknown keys
are ignored.

`archive` is retired. Closing a task sets `status: done` and leaves the file where it
is: paths stay valid for everything that links to them, and the closed task — the one
file that records what was verified and what was deliberately left undone — stays
visible. Readers still load a legacy `archive/` directory if one exists; nothing new
is ever written there. `ls` hides `done` unless you pass `--all` or ask for it by
status.

## Parsing rules

Frontmatter is read with a flat YAML subset: scalars, `- item` lists, `#` comments.
A key with an empty value reads as an empty list.

**Writes are surgical.** The CLI replaces a single frontmatter line by regex and
never reserializes the block, so comments, ordering and fields it does not
understand survive untouched.

## Nudges

Derived from disk state at session start, not from lifecycle events — nothing has
to have fired for the state to be correct.

| Condition | Signal |
| --- | --- |
| Abandoned task | task file mtime older than `stale_days` |
| Unwritten log | a file in `git diff --name-only HEAD` is newer than the task file |

Nudges only remind. Nothing is written automatically.

`TRAIL_DISABLED=1` makes every command a no-op, so a one-off session in someone
else's repo is never hijacked.

## Backlog

```markdown
- [ ] ask backend whether AppPageType=18 is empty #report-api
- [x] archive the temporary PoC checklist #report-api
```

`backlog.md` holds deferred small work — never work in progress. It is a sink, not a
tracker: a flat markdown list, no frontmatter, no ids, no lifecycle beyond the box.
`trail status` reports the open count and never the contents; injecting them would
turn the file into a graveyard that rots in every prompt.

Each line is a checkbox and carries the `#<task-slug>` of the task it came out of, so
a line can be traced back to its work and queried from outside. `trail backlog` tags
with the active task unless you pass `--untagged`.

`trail done` deletes the **ticked** lines tagged with the closing task — they are
already recorded in the task file and the commits — and reports the unticked ones
instead of touching them. That asymmetry is deliberate: the first real close left two
open items in the backlog on purpose ("error path untested", "never tried on
Android"), and deleting those would have destroyed the only record of them.

Growth is expected; the failure signal is the opposite. Backlog lines describing work
that was already done mean the boundary leaked and T0 started paying a tax. Lines
describing *measurements* mean `## Notes` is not being used.
