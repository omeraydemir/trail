---
id: field-use-revisions
title: "Field-use revisions: a task file you can read, a CLI worth reading"
level: T2
status: done
started: 2026-09-12
links:
  - spec/FORMAT.md
  - bin/trail
  - skills/trail/SKILL.md
  - templates/_template.md
---
# Field-use revisions

## Goal
A task file answers "what is done, where am I" within its first screen, the CLI's
output is worth reading, and related tasks from one `plan` run find each other —
all of it driven by what broke in the first real project (Gocust.MAUI, 5 tasks,
28 backlog lines, 2026-09-09..12).

## Out of Scope
- Migrating the Gocust.MAUI ledger. It is a live working repo; this repo defines
  the target format, the migration is a separate call.
- A format validator / `trail lint`. Hand-editing is allowed precisely so the
  format does not need policing yet.
- The other 16 Obsidian checkbox statuses, `[?]` and `[!]` included — `[?]`
  collides with `## Open Questions`, `[!]` with `status: blocked`.
- Obsidian vault configuration. The format stays Dataview-friendly; the plugin
  setup is the user's side.
- Per-item backlog commands beyond what `done` needs.

## Plan

### A. Format contract — `spec/FORMAT.md`, `templates/_template.md`
- [x] Section order: `Goal → Out of Scope → Plan → Status → Notes → Decision Log → Open Questions` [completion:: 2026-09-12]
- [x] `## Plan` and `## Notes` ship in the template at every level; `## Plan` stops being a T2 hand-addition [completion:: 2026-09-12]
- [x] `title` is always quoted on write — 2 of the 5 real task files were invalid YAML (`title: Rapor: pivot matrisi`) [completion:: 2026-09-12]
- [x] `group:` frontmatter field: optional, slug-valued, no index file, queryable from Dataview [completion:: 2026-09-12]
- [x] Plan items are checkboxes — `[ ]` todo · `[/]` written, not verified · `[x]` verified · `[-]` cancelled; `[x]` carries `[completion:: YYYY-MM-DD]` [completion:: 2026-09-12]
- [x] Decision log entry becomes a scannable title line plus `why:` / `dropped:` sub-bullets [completion:: 2026-09-12]
- [x] `archive/` retired: `done` sets `status: done` and the file stays in `tasks/`; the `archive` config key goes [completion:: 2026-09-12]
- [x] Backlog line format: `- [ ] <item> #<task-slug>` [completion:: 2026-09-12]

### B. CLI — `bin/trail`
- [x] `trail note "<text>"` — append a dated line to `## Notes` (the section has no other writer) [completion:: 2026-09-12]
- [x] `trail set group <value>` and `trail start --group` [completion:: 2026-09-12]
- [x] `log` writes the new multi-line entry shape [completion:: 2026-09-12]
- [x] `done`: no file move; delete `[x]` backlog lines tagged with the task, report the `[ ]` ones instead of touching them [completion:: 2026-09-12]
- [x] `ls`: progress column (`4/6`), sections by `group`, `done` hidden unless `--all`, titles no longer truncated [completion:: 2026-09-12]
- [x] `board`: stop cutting titles mid-word; the `done` column fills now that nothing is archived [completion:: 2026-09-12]
- [x] `status`: decision title lines only, `--full` for the bodies — today it prints ~4k characters every session [completion:: 2026-09-12]
- [x] Colour on headings and status values; off when `NO_COLOR` is set or stdout is not a tty [completion:: 2026-09-12]

### C. Skill — `skills/trail/SKILL.md`
- [x] "Never hand-edit" → "prefer the CLI; hand-edit when it cannot express what you mean, and do not break the format" [completion:: 2026-09-12]
- [x] `plan` produces ONE task by default; a second needs a stated reason, a third needs the user's approval; a source document's sections are not task boundaries [completion:: 2026-09-12]
- [x] `## Notes` gets one sentence: the section exists, it is free-form, no format [completion:: 2026-09-12]
- [x] The decision-vs-note test: rejected an alternative → decision log; everything else → note [completion:: 2026-09-12]
- [x] Checkbox semantics and `[completion:: ]` [completion:: 2026-09-12]
- [x] Resume with `/trail <slug>` so chat titles stay distinguishable [completion:: 2026-09-12]

### D. Verification
- [x] `test_trail.py` green, with cases for the new writers [completion:: 2026-09-12]
- [x] Re-read the Gocust.MAUI task files against the new format and confirm each original complaint is answered [completion:: 2026-09-12]

## Status
A, B, C and D shipped; 9 tests green plus a scratch-repo smoke run. The Gocust.MAUI ledger is NOT migrated - it still carries the old one-line decision log, prose plans and two invalid-YAML titles. Next: decide whether to migrate it (mechanical for titles and backlog tags, a judgement call for splitting the 5 files back into one).

## Notes

- **2026-09-12** · Verification pass against the 10 complaints from the Gocust.MAUI run: 5 files with no relation -> group: + one-task default; unreadable file -> section order + checkboxes; closed task lost in archive/ -> archive retired; formless CLI output -> colour, PLAN column, group sections, decision titles only; board hiding done -> column fills; Obsidian failing on unquoted title -> yaml_quote on every write; unscannable log -> multi-line entries; backlog out of control -> ## Notes absorbs findings, checkbox + #tag, done sweeps ticked lines; every chat titled Trail -> /trail <slug>; model hand-editing against the rule -> hand-editing is now allowed. All ten answered.

## Decision Log
- **2026-09-12** · four checkbox symbols, not the full Obsidian set
  - **why:** `[ ]` todo, `[/]` written-not-verified, `[x]` verified, `[-]` cancelled. Twenty symbols means twenty choices per item and the model picks inconsistently; these four are the ones the real ledger actually needed.
  - **dropped:** `[?]` and `[!]` — the first duplicates `## Open Questions`, the second duplicates `status: blocked`.
- **2026-09-12** · `[x]` means verified; written-but-unproven is `[/]`
  - **why:** report-3 carried "Plan 5 YAZILDI, commit YOK, cihazda denenmedi" in prose because neither `[ ]` nor `[x]` was true. The distinction existed in the work before it existed in the format.
  - **dropped:** a single `[x]` plus a caveat in `## Status` — that is the arrangement that forced the reader to cross-reference two sections to learn what was done.
- **2026-09-12** · `group:` frontmatter field replaces slug-prefix grouping
  - **why:** the user has no GUI and queries the ledger from Obsidian Dataview; a frontmatter field is the query surface, a filename convention is not. Renaming a group should not rename five files.
  - **dropped:** grouping `ls` by slug prefix (zero schema change, but nothing to query and rename churn), and the parent/index task the format still rightly forbids — `group:` is a label, not a hand-written child list, so it cannot go stale.
- **2026-09-12** · `archive/` retired; `done` tasks stay in `tasks/`
  - **why:** the single most useful file in the real ledger was the closed `report-2-tablo` (verified / not verified / unresolved / out of scope), and archiving hid it: `board` showed `done (0)` throughout. Paths also stop moving, which every link into the file depends on.
  - **dropped:** keeping `archive/` and adding a `--archived` flag to the readers — the flag would be off by default, so the useful file stays hidden by default.
- **2026-09-12** · hand-editing a task file is allowed
  - **why:** the ban plus a CLI that cannot express everything put the model in a bind it resolved by editing anyway, silently. A rule that is broken to get work done is worse than no rule. Preference stays with the CLI; the only obligation is not breaking the format.
  - **dropped:** keeping the ban and writing a validator to enforce it — that is a second tool to maintain in order to defend a rule nobody could follow.
- **2026-09-12** · `## Notes` exists with no rules attached
  - **why:** the backlog grew to 28 lines mostly because measurements and discoveries had nowhere else to go. The section absorbs them. Prescribing its shape would recreate the pressure that made the model invent headings of its own.
  - **dropped:** a structured findings format; also leaving the section out and letting the decision log carry everything — it already runs 400-800 characters an entry.
- **2026-09-12** · decision log entries become multi-line
  - **why:** a title line you can scan, then `why:` / `dropped:` as sub-bullets. The single-line form hid where each field started. It also gives `trail status` something short to print instead of five full entries.
  - **dropped:** bolding the labels inside the one-line form — cheaper, but the eye still has to read the whole sentence to find the boundary.
- **2026-09-12** · `done` deletes only `[x]` backlog lines tagged with the task
  - **why:** `report-2` closed leaving two deliberate open items in the backlog ("error path untested", "never tried on Android"). Deleting those would have destroyed the only record. Finished items are already recorded in the task file and the commits.
  - **dropped:** deleting every line carrying the tag, and moving them into the task file — the first loses live work, the second buries it where nobody looks for deferred items.
- **2026-09-12** · `plan` defaults to one task
  - **why:** the 5-file split failed the format's own splitting test — report-4's scope references report-3 §4 and report-2, report-5 references report-2. What actually drove the split was the source document's phase headings leaking into the ledger.
  - **dropped:** tightening the wording of the existing test alone — the test was already there and still answered "no"; the default has to change, not the prose.
- **2026-09-12** · chat titles fixed by typing `/trail <slug>`, not by code
  - **why:** every resumed session was titled "Trail" because the first message was bare `/trail`. Passing the slug makes the title distinguishable at zero cost.
  - **dropped:** having the skill set the session title through the desktop MCP tool — that tool exists in Claude Code desktop only, and the skill has to work everywhere.
- **2026-09-12** · the template quotes {{title}} even though cmd_start re-quotes the field anyway
  - **why:** verified both ways in a scratch repo: substitution then set_field produces one correctly escaped value, no double quoting, even for a title containing a quote character. The quotes in the template are documentation for whoever opens it
  - **dropped:** leaving the placeholder bare to avoid the appearance of redundancy — a user editing the template would have no hint that the field must be quoted

## Open Questions
