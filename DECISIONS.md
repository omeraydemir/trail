# Decisions

Distilled from task decision logs at `trail done`.

## trail'i kendi üstünde kullan

_2026-09-09 · T1 · bootstrap-trail_

- 2026-09-09 · CLI v1 formatı 2 hafta elle kullanmadan yazıldı · why: elle kurulum istenmedi; tek kullanıcı olduğu için format değişikliği ucuz · dropped: spec'in önerdiği 2 haftalık elle kullanım fazı
- 2026-09-09 · Kurulum ayrı clone yerine çalışma reposuna symlink · why: tek kullanıcı; düzenleme anında canlı, iki kopya senkronu yok · dropped: ~/.local/share/trail'e ikinci clone (README'deki genel yol)
- 2026-09-09 · SKILL.md hedefi ajana göre ayrışıyor: .claude/skills vs .agents/skills · why: Claude Code .agents/skills okumuyor, belgeyle doğrulandı; tek evrensel yol yok · dropped: .agents/skills'i tek kaynak varsaymak

## first-use revisions

_2026-09-09 · T2 · first-use-revisions_

- 2026-09-09 · trail carries context across sessions; the decision log is the mechanism, not the goal · why: the first design argument was built on 'what is the unit of distillation' and reached the wrong answer · dropped: positioning trail as an ADR/decision-record manager
- 2026-09-09 · No relation field; order between split tasks goes in the slug prefix · why: sorting is (status, id), so the prefix carries order for free — no cycle check, no stale cross-reference · dropped: an after: field (a dependency graph, explicitly out of scope), and a parent/index file
- 2026-09-09 · Splitting test is context, not size: does phase 3 need phase 1 in your head? · why: splitting a task splits the context you were trying to carry; ten phases can still be one T2 · dropped: a phase-count or duration threshold
- 2026-09-09 · Two axes: size decides whether it gets a file, deferral decides whether it needs a trace · why: the missing box was small-and-deferred; one axis pushed those items into T0, where they vanished · dropped: treating the backlog as T0's home — T0 has no home, and giving it one ends its freeness
- 2026-09-09 · plan can never produce a T0 item · why: planning is by definition deferral, so its output has exactly two buckets: a task file or a backlog line · dropped: a third bucket left in the reply as 'T0, no file needed'
- 2026-09-09 · Long designs live in a linked reference document under docs/, not in ## Plan · why: the task file is injected every session; a two-week design would pollute all of them · dropped: putting the document inside .trail/ (different lifetime), and generating one on every plan run
- 2026-09-09 · links: kept and given a writer instead of being deleted · why: the missing part was the write path, not the field; it is the bridge to the reference document · dropped: deleting the field under the 'no field without a writer' rule
- 2026-09-09 · init creates .trail/backlog.md instead of waiting for first use · why: a sink nobody can see is a sink nobody empties; init's job is to show the whole system · dropped: lazy creation on first 'trail backlog'
- 2026-09-09 · init fills gaps in already-initialised repos; status nudges when the scaffold is behind · why: init is idempotent but nothing told the user to re-run it, so a new scaffold file stayed invisible in old repos — and this repeats on every future addition · dropped: a migration/upgrade command, and background scanning of repos
- 2026-09-09 · README's '--json everywhere' claim narrowed to the three commands that have it · why: board and backlog are shaped for a terminal, and nothing consumes their JSON · dropped: adding --json to board and backlog to make the old sentence true

## Field-use revisions: a task file you can read, a CLI worth reading

_2026-09-12 · T2 · field-use-revisions_

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
