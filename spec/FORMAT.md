# Format contract

Everything trail does is defined by these files. The CLI is replaceable; the format
is the product.

## Layout

```
.trail/
  config.yml          optional; defaults apply when absent
  _template.md        task template, user-editable
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
- `level` is `T1` or `T2`. T0 tasks have no file at all.
- `links` is a flat list of repo paths, optionally `path:line`. Not validated.

### Decision log line

```
- YYYY-MM-DD · <decision> · why: <reason> · dropped: <alternative>
```

`why:` and `dropped:` are optional but `dropped:` is the reason the format exists.

## Template placeholders

`trail start` substitutes `{{id}}` `{{title}}` `{{level}}` `{{status}}` `{{date}}`.
**Unrecognized placeholders are left untouched**, so custom fields are safe.

## Config

Flat YAML. Keys: `dir` `archive` `decisions` `template` `stale_days`. Unknown keys
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
