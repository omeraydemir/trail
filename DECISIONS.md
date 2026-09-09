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
