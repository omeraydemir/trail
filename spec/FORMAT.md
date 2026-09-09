# Format contract

Everything trail does is defined by these files. The CLI is replaceable; the format
is the product.

## Layout

```
.trail/
  config.yml          optional; defaults apply when absent
  _template.md        task template, user-editable
  backlog.md          small items; a flat list, no frontmatter, no lifecycle
  tasks/<slug>.md     active tasks — scaffolding, dies with the task
  archive/<slug>.md   closed tasks; moved, never deleted
DECISIONS.md          distilled decisions — permanent, versioned with the code
```

`trail init` also drops `SKILL.md` where the repo's agents look for project skills:
`.claude/skills/trail/` for Claude Code, `.agents/skills/trail/` for Codex, Cursor and
Gemini CLI. There is no single path every agent reads.

`DECISIONS.md` sits outside `.trail/` on purpose: if a user gitignores `.trail/`,
the permanent artifact still gets committed.

`.trail/` is committed by default. Solo users who want tasks off git add it to
`.gitignore`; the two-lifetime split survives either choice.

## Task file

```markdown
---
id: push-notification-deeplink
title: push notification deeplink
level: T1
status: active
started: 2026-08-27
links:
  - src/Notifications/DeepLinkHandler.cs:120
---
# push notification deeplink

## Goal
## Out of Scope
## Decision Log
## Status
## Open Questions
```

`## Plan` is added by hand for T2.

### Core fields

`id` · `title` · `level` · `status` are the only fields the CLI reads. Everything
else is free — add fields to `_template.md` and nothing breaks.

- `status` is one of `open` · `active` · `blocked` · `done`. The set is closed:
  board columns derive from it.
- `level` is `T1` or `T2`. T0 has no task file and no representation anywhere:
  small work being done now leaves no trace. `backlog.md` holds the other case,
  small work that is deferred.
- `links` is a flat list of repo paths, optionally `path:line`. Not validated.
  It is how a task points at the design document or the code it concerns.

There is no relation between tasks: no parent, no subtask, no dependency field.
Ordering between related tasks lives in the slug (`auth-1-provider`,
`auth-2-session`), which `ls` sorts for free.

### Decision log line

```
- YYYY-MM-DD · <decision> · why: <reason> · dropped: <alternative>
```

`why:` and `dropped:` are optional but `dropped:` is the reason the format exists.

## What belongs in a task file

The task file is injected into every session. That is the whole constraint, and the
division falls out of it:

| | Lives in | On session start |
| --- | --- | --- |
| What you must hold in your head each session — goal, boundary, position, decisions | the task file | injected |
| What you consult when you reach that part — designs, specs, long plans | a reference document | linked, not injected |

`links:` is that bridge. A two-week design poured into `## Plan` breaks both halves:
the file stops answering "where am I", and the detail is re-injected every session.

A reference document lives under the repo's own docs convention, never inside
`.trail/` — same reason `DECISIONS.md` sits outside it: a different lifetime. trail
links such a document; it does not own it.

Drift between the two is not a real risk, because they do not overlap: the document
holds the design and changes rarely, the task file holds the position and changes
constantly. A design change is one `trail log` line (why) plus a document edit (what
it now is).

## Splitting work across task files

The test is not size and not phase count:

> When you sit down to phase 3, do you need phase 1's status and decisions in your
> head?

- **Yes** → one T2 task, phases as a checklist under `## Plan`. Ten phases still
  means one file: splitting it splits the context you were trying to carry.
- **No** → separate tasks.

When you do split, order and grouping go in the **slug prefix**, not in a field:
`auth-1-provider`, `auth-2-session`, `auth-3-migration`. Tasks sort by `(status, id)`,
so the prefix carries the order for free.

There is deliberately no relation field (`after:`, parent, subtask) and no index file
pointing at children: a hand-written cross-reference goes stale within the hour.

## Template placeholders

`trail start` substitutes `{{id}}` `{{title}}` `{{level}}` `{{status}}` `{{date}}`.
**Unrecognized placeholders are left untouched**, so custom fields are safe.

## Config

Flat YAML. Keys: `backlog` `dir` `archive` `decisions` `template` `stale_days`. Unknown keys
are ignored.

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

`backlog.md` holds deferred small work — never work in progress, never work that
is finished. It is a sink, not a tracker: a flat markdown list, no frontmatter, no
status, no ids. Nothing distills it, nothing nudges about it, and no command
operates on a single item — promotion is `trail start` plus deleting the line by
hand. `trail status` reports the item count and never the contents; injecting them
would turn the file into a graveyard that rots in every prompt.

Growth is expected; the failure signal is the opposite. Backlog lines describing
work that was already done mean the boundary leaked and T0 started paying a tax.
